# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

# Standard Library
import os
from typing import Any

# AWS Libraries
from aws_cdk import ArnFormat, Aws, RemovalPolicy, Stack, aws_ec2, aws_iam, aws_logs
from chalice.cdk import Chalice
from constructs import Construct

# CMS Common Library
from cms_common.config.stack_inputs import SolutionConfigInputs
from cms_common.constructs.vpc_construct import VpcConstruct
from cms_common.policy_generators.ec2_vpc import generate_ec2_vpc_policy

# Connected Mobility Solution on AWS
from .simulator import SimulatorConstruct
from .storage import StorageConstruct


class VSApiConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        stack_id: str,
        solution_config_inputs: SolutionConfigInputs,
        storage_construct: StorageConstruct,
        simulator_construct: SimulatorConstruct,
        cloudfront_domain_name: str,
        user_pool_arn: str,
        api_gateway_stage: str,
        vpc_construct: VpcConstruct,
        **kwargs: Any,
    ):
        super().__init__(scope, stack_id, **kwargs)

        self.api_log_group = aws_logs.LogGroup(
            self,
            "vs-api-log-group",
            removal_policy=RemovalPolicy.RETAIN,
            retention=aws_logs.RetentionDays.THREE_MONTHS,
        )

        self.vs_api_lambda_role = aws_iam.Role(
            self,
            "vs-api-lambda-role",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            path="/",
            inline_policies={
                "api-cloudwatch-logs-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "logs:CreateLogGroup",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents",
                            ],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="logs",
                                    resource="log-group",
                                    resource_name="/aws/lambda/*",
                                    arn_format=ArnFormat.COLON_RESOURCE_NAME,
                                )
                            ],
                        ),
                    ]
                ),
                "dynamodb-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "dynamodb:GetItem",
                                "dynamodb:Scan",
                                "dynamodb:PutItem",
                                "dynamodb:DeleteItem",
                                "dynamodb:UpdateItem",
                            ],
                            resources=[
                                storage_construct.devices_types_table.table_arn,
                                storage_construct.simulations_table.table_arn,
                                storage_construct.templates_table.table_arn,
                            ],
                        )
                    ]
                ),
                "state-machine-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=["states:StartExecution", "states:StopExecution"],
                            resources=[
                                simulator_construct.simulator_state_machine.state_machine_arn,
                                Stack.of(self).format_arn(
                                    service="states",
                                    resource="execution",
                                    resource_name=f"{simulator_construct.simulator_state_machine.state_machine_name}:*",
                                    arn_format=ArnFormat.COLON_RESOURCE_NAME,
                                ),
                            ],
                        ),
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "states:ListStateMachines",
                            ],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="states",
                                    resource="stateMachine",
                                    resource_name="*",
                                    arn_format=ArnFormat.COLON_RESOURCE_NAME,
                                )
                            ],
                        ),
                    ]
                ),
                "iot-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=["iot:DeleteThing"],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="iot",
                                    resource="thing",
                                    resource_name="*",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                            ],
                        ),
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=["iot:DeletePolicy"],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="iot",
                                    resource="policy",
                                    resource_name="*",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                            ],
                        ),
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "iot:DetachThingPrincipal",
                                "iot:ListThings",
                                "iot:ListThingPrincipals",
                                "iot:ListAttachedPolicies",
                            ],
                            resources=["*"],
                        ),
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "iot:DetachPolicy",
                                "iot:DeleteCertificate",
                            ],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="iot",
                                    resource="cert",
                                    resource_name="*",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                            ],
                        ),
                    ]
                ),
                "tags-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "tag:GetResources",
                            ],
                            resources=["*"],
                        )
                    ]
                ),
                "secrets-manager-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "secretsmanager:DeleteSecret",
                            ],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="secretsmanager",
                                    resource="secret",
                                    resource_name="*",
                                    arn_format=ArnFormat.COLON_RESOURCE_NAME,
                                ),
                            ],
                        )
                    ]
                ),
                "ec2-vpc-policy": generate_ec2_vpc_policy(
                    self,
                    vpc_construct=vpc_construct,
                    subnet_selection=vpc_construct.private_subnet_selection,
                    authorized_service="lambda.amazonaws.com",
                ),
            },
        )

        cross_origin_domain = f"https://{cloudfront_domain_name}"

        self.chalice = Chalice(
            self,
            "vs-api-chalice",
            source_dir=os.path.join(
                os.path.dirname(__file__),
                os.pardir,
                os.pardir,
                "api",
                "vs_api",
            ),
            stage_config={
                "environment_variables": {
                    "DYN_DEVICE_TYPES_TABLE": storage_construct.devices_types_table.table_name,
                    "DYN_TEMPLATES_TABLE": storage_construct.templates_table.table_name,
                    "DYN_SIMULATIONS_TABLE": storage_construct.simulations_table.table_name,
                    "SIMULATOR_STATE_MACHINE_NAME": simulator_construct.simulator_state_machine.state_machine_name,
                    "CROSS_ORIGIN_DOMAIN": cross_origin_domain,
                    "USER_POOL_ARN": user_pool_arn,
                    "USER_AGENT_STRING": solution_config_inputs.get_user_agent_string(),
                },
                "manage_iam_role": False,
                "iam_role_arn": self.vs_api_lambda_role.role_arn,
                "api_gateway_stage": api_gateway_stage,
                "api_gateway_endpoint_type": "REGIONAL",
                "subnet_ids": vpc_construct.vpc.select_subnets(
                    vpc_construct.private_subnet_selection
                ).get("subnetIds"),
                "security_group_ids": [
                    aws_ec2.SecurityGroup(
                        self,
                        "security-group",
                        vpc=vpc_construct.vpc,
                        allow_all_outbound=True,  # NOSONAR
                    ).security_group_id
                ],
            },
        )

        self.rest_api_endpoint = f"https://{self.chalice.sam_template.get_resource('RestAPI').ref}.execute-api.{Stack.of(self).region}.{Aws.URL_SUFFIX}/{api_gateway_stage}"
