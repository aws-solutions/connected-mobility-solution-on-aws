# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library

# AWS Libraries
from aws_cdk import (
    ArnFormat,
    Duration,
    Stack,
    aws_ec2,
    aws_iam,
    aws_iot,
    aws_lambda,
    aws_logs,
)
from constructs import Construct

# CMS Common Library
from cms_common.config.resource_names import ResourceName, ResourcePrefix
from cms_common.config.stack_inputs import SolutionConfigInputs
from cms_common.constructs.vpc_construct import VpcConstruct
from cms_common.policy_generators.cloudwatch import (
    generate_lambda_cloudwatch_logs_policy_document,
)
from cms_common.policy_generators.ec2_vpc import generate_ec2_vpc_policy
from cms_common.policy_generators.kms import generate_kms_policy_statement

# Connected Mobility Solution on AWS
from ...handlers.provisioning.function.lib.dynamo_table_name_key_enum import (
    DynamoTableNameKey,
)
from .provisioning_database import ProvisioningDBResources


class InitialConnectionConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        dependency_layer: aws_lambda.LayerVersion,
        provisioning_db_resources: ProvisioningDBResources,
        app_unique_id: str,
        solution_config_inputs: SolutionConfigInputs,
        vpc_construct: VpcConstruct,
    ) -> None:
        super().__init__(scope, construct_id)

        initial_connection_lambda_function_name = ResourceName.hyphen_separated(
            prefix=ResourcePrefix.hyphen_separated(
                app_unique_id=app_unique_id,
                module_name=solution_config_inputs.module_short_name,
            ),
            name="initial-connection",
        )

        initial_connection_lambda_role = aws_iam.Role(
            self,
            "lambda-role",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            path="/",
            inline_policies={
                "cloudwatch-logs-policy": generate_lambda_cloudwatch_logs_policy_document(
                    self, lambda_function_name=initial_connection_lambda_function_name
                ),
                "dynamodb-provisioned-vehicles-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "dynamodb:UpdateItem",
                            ],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="dynamodb",
                                    resource="table",
                                    resource_name=provisioning_db_resources.provisioned_vehicles_table.table_name,
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                            ],
                        ),
                        generate_kms_policy_statement(
                            self,
                            kms_encryption_key_id=provisioning_db_resources.provisioned_vehicles_table_kms_key.key_id,
                            allow_encrypt=True,
                        ),
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

        # Lambda function which will trigger on vehicle connection
        initial_connection_lambda_function = aws_lambda.Function(
            self,
            "lambda-function",
            function_name=initial_connection_lambda_function_name,
            code=aws_lambda.Code.from_asset("dist/lambda/provisioning.zip"),
            description="CMS Provisioning initial connection lambda function",
            handler="function.initial_connection.handler",
            runtime=aws_lambda.Runtime.PYTHON_3_10,
            role=initial_connection_lambda_role,
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
            timeout=Duration.minutes(1),
            environment={
                DynamoTableNameKey.PROVISIONED_VEHICLES_TABLE_NAME.value: provisioning_db_resources.provisioned_vehicles_table.table_name,
                "USER_AGENT_STRING": solution_config_inputs.get_user_agent_string(),
            },
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
        )

        initial_connection_lambda_function.add_permission(
            id="iot-invoke-initial-connection-lambda-permission",
            principal=aws_iam.ServicePrincipal("iot.amazonaws.com"),
            action="lambda:InvokeFunction",
            source_account=Stack.of(self).account,
        )

        aws_iot.CfnTopicRule(
            self,
            "iot-initial-connection-lambda-rule",
            rule_name=ResourceName.underscore_separated(
                prefix=ResourcePrefix.only_underscore_separated(
                    app_unique_id=app_unique_id,
                    module_name=solution_config_inputs.module_short_name,
                ),
                name="iot_initial_connection",
            ),
            topic_rule_payload=aws_iot.CfnTopicRule.TopicRulePayloadProperty(
                sql="SELECT * FROM 'vehicleactive/#'",
                description="Trigger lambda to updated ProvisionedVehicles record on vehicle initial connection.",
                actions=[
                    aws_iot.CfnTopicRule.ActionProperty(
                        lambda_=aws_iot.CfnTopicRule.LambdaActionProperty(
                            function_arn=initial_connection_lambda_function.function_arn,
                        )
                    )
                ],
            ),
        )
