# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any, List

# AWS Libraries
from aws_cdk import ArnFormat, Duration, Stack, aws_ec2, aws_iam, aws_lambda, aws_logs
from constructs import Construct

# CMS Common Library
from cms_common.config.resource_names import ResourceName, ResourcePrefix
from cms_common.config.stack_inputs import SolutionConfigInputs
from cms_common.constructs.vpc_construct import VpcConstruct
from cms_common.policy_generators.cloudwatch import (
    generate_lambda_cloudwatch_logs_policy_document,
)
from cms_common.policy_generators.ec2_vpc import generate_ec2_vpc_policy
from cms_common.policy_generators.kms import generate_kms_policy_statement_from_key_id


class IncomingAlertsConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_unique_id: str,
        solution_config_inputs: SolutionConfigInputs,
        dependency_layer: aws_lambda.LayerVersion,
        notifications_table_name: str,
        notifications_table_key_id: str,
        sns_topic_prefix: str,
        vpc_construct: VpcConstruct,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        alerts_lambda_name = ResourceName.hyphen_separated(
            prefix=ResourcePrefix.hyphen_separated(
                app_unique_id=app_unique_id,
                module_name=solution_config_inputs.module_short_name,
            ),
            name="create-alerts",
        )

        self.alerts_lambda = aws_lambda.Function(
            self,
            "create-alerts-lambda",
            function_name=alerts_lambda_name,
            code=aws_lambda.Code.from_asset("dist/lambda/create_alerts.zip"),
            description="CMS Alerts Lambda Function",
            environment={
                "USER_AGENT_STRING": solution_config_inputs.get_user_agent_string(),
                "NOTIFICATIONS_TABLE_NAME": notifications_table_name,
                "SNS_TOPIC_PREFIX": sns_topic_prefix,
            },
            handler="app.main.handler",
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            timeout=Duration.seconds(30),
            role=aws_iam.Role(
                self,
                "alerts-lambda-role",
                assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
                inline_policies={
                    "cloudwatch-policy": generate_lambda_cloudwatch_logs_policy_document(
                        self, alerts_lambda_name
                    ),
                    "dynamodb-policy": aws_iam.PolicyDocument(
                        statements=[
                            aws_iam.PolicyStatement(
                                effect=aws_iam.Effect.ALLOW,
                                actions=[
                                    "dynamodb:PutItem",
                                ],
                                resources=[
                                    Stack.of(self).format_arn(
                                        service="dynamodb",
                                        resource="table",
                                        resource_name=f"{notifications_table_name}",
                                        arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                    ),
                                ],
                            ),
                            generate_kms_policy_statement_from_key_id(
                                self, notifications_table_key_id, False
                            ),
                        ]
                    ),
                    "ec2-policy": generate_ec2_vpc_policy(
                        self,
                        vpc_construct=vpc_construct,
                        subnet_selection=vpc_construct.private_subnet_selection,
                        authorized_service="lambda.amazonaws.com",
                    ),
                },
            ),
            layers=[dependency_layer],
            vpc=vpc_construct.vpc,
            vpc_subnets=vpc_construct.private_subnet_selection,
            security_groups=[
                aws_ec2.SecurityGroup(
                    self,
                    "security-group",
                    vpc=vpc_construct.vpc,
                    allow_all_outbound=True,  # NOSONAR
                )
            ],
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
        )

    def add_to_alerts_lambda_role_policy(
        self, effect: aws_iam.Effect, actions: List[str], resources: List[str]
    ) -> None:
        self.alerts_lambda.add_to_role_policy(
            statement=aws_iam.PolicyStatement(
                effect=effect, actions=actions, resources=resources
            )
        )
