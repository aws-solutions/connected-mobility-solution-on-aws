# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import dataclasses
from typing import Any, Tuple

# Third Party Libraries
from aws_cdk import (
    ArnFormat,
    Duration,
    NestedStack,
    Stack,
    aws_dynamodb,
    aws_iam,
    aws_iot,
    aws_kms,
    aws_lambda,
    aws_logs,
    aws_ssm,
)
from constructs import Construct
from dataclass_type_validator import dataclass_validate  # type: ignore

# Connected Mobility Solution on AWS
from ...config.constants import VPConstants
from ...handlers.provisioning.lib.dynamo_table_name_key_enum import DynamoTableNameKey
from ..lib.policy_generators import (
    generate_kms_policy_statement,
    generate_lambda_cloudwatch_logs_policy_document,
)


@dataclass_validate
@dataclasses.dataclass(frozen=True)
class ProvisioningLambdaFunctions:
    pre_provisioning_lambda: aws_lambda.Function
    post_provisioning_lambda: aws_lambda.Function
    initial_connection_lambda: aws_lambda.Function


@dataclass_validate
@dataclasses.dataclass(frozen=True)
class ProvisioningDBResources:
    authorized_vehicles_table_kms_key: aws_kms.Key
    authorized_vehicles_table: aws_dynamodb.Table
    provisioned_vehicles_table_kms_key: aws_kms.Key
    provisioned_vehicles_table: aws_dynamodb.Table


class ProvisioningLambdasStack(NestedStack):
    def __init__(
        self,
        scope: Construct,
        stack_id: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, stack_id, **kwargs)

        provisioning_db_resources = self.setup_dynamodb_tables()
        self.authorized_vehicles_table_kms_key = (
            provisioning_db_resources.authorized_vehicles_table_kms_key
        )
        self.authorized_vehicles_table = (
            provisioning_db_resources.authorized_vehicles_table
        )
        self.provisioned_vehicles_table_kms_key = (
            provisioning_db_resources.provisioned_vehicles_table_kms_key
        )
        self.provisioned_vehicles_table = (
            provisioning_db_resources.provisioned_vehicles_table
        )

        lambda_functions = self.setup_provisioning_lambdas()
        self.pre_provisioning_lambda = lambda_functions.pre_provisioning_lambda
        self.post_provisioning_lambda = lambda_functions.post_provisioning_lambda
        self.initial_connection_lambda = lambda_functions.initial_connection_lambda
        (
            self.thing_event_topic_rule,
            self.initial_connection_topic_rule,
        ) = self.setup_iot_core_rules()

        aws_ssm.StringParameter(
            self,
            "pre-provisioning-lambda-arn-value",
            string_value=self.pre_provisioning_lambda.function_arn,
            description="Arn for the pre provisioning lambda function",
            parameter_name=f"/{VPConstants.STAGE}/{VPConstants.APP_NAME}/arns/pre-provisioning-lambda-arn",
        )

        aws_ssm.StringParameter(
            self,
            "authorized-vehicles-table-arn-value",
            string_value=self.authorized_vehicles_table.table_arn,
            description="Table arn for the authorized vehicles table",
            parameter_name=f"/{VPConstants.STAGE}/{VPConstants.APP_NAME}/arns/authorized-vehicles-table-arn",
        )

        # This is necessary for mypy to not complain, since encryption_key can be of type IKey or None
        if self.authorized_vehicles_table.encryption_key is not None:
            aws_ssm.StringParameter(
                self,
                "authorized-vehicles-table-encyrption-key-arn-value",
                string_value=self.authorized_vehicles_table.encryption_key.key_arn,
                description="Encryption key arn for the authorized vehicles table",
                parameter_name=f"/{VPConstants.STAGE}/{VPConstants.APP_NAME}/arns/authorized-vehicles-encryption-key-arn",
            )

        aws_ssm.StringParameter(
            self,
            "authorized-vehicles-table-name",
            string_value=self.authorized_vehicles_table.table_name,
            description="Table name for the authorized vehicles table",
            parameter_name=f"/{VPConstants.STAGE}/{VPConstants.APP_NAME}/table-names/authorized-vehicles-table-name",
        )

    def setup_dynamodb_tables(self) -> ProvisioningDBResources:
        authorized_vehicles_table_kms_key = aws_kms.Key(
            self,
            "authorized-vehicles-table-kms-key",
            enable_key_rotation=True,
        )
        authorized_vehicles_table = aws_dynamodb.Table(
            self,
            "authorized-vehicles-table",
            partition_key=aws_dynamodb.Attribute(
                name="vin",
                type=aws_dynamodb.AttributeType.STRING,
            ),
            billing_mode=aws_dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption_key=authorized_vehicles_table_kms_key,
            point_in_time_recovery=True,
        )

        provisioned_vehicles_table_kms_key = aws_kms.Key(
            self,
            "provisioned-vehicles-table-kms-key",
            enable_key_rotation=True,
        )
        provisioned_vehicles_table = aws_dynamodb.Table(
            self,
            "provisioned-vehicles-table",
            partition_key=aws_dynamodb.Attribute(
                name="vin",
                type=aws_dynamodb.AttributeType.STRING,
            ),
            sort_key=aws_dynamodb.Attribute(
                name="certificate_id",
                type=aws_dynamodb.AttributeType.STRING,
            ),
            billing_mode=aws_dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption_key=provisioned_vehicles_table_kms_key,
            point_in_time_recovery=True,
        )

        return ProvisioningDBResources(
            authorized_vehicles_table_kms_key=authorized_vehicles_table_kms_key,
            authorized_vehicles_table=authorized_vehicles_table,
            provisioned_vehicles_table_kms_key=provisioned_vehicles_table_kms_key,
            provisioned_vehicles_table=provisioned_vehicles_table,
        )

    def setup_provisioning_lambdas(
        self,
    ) -> ProvisioningLambdaFunctions:
        pre_provisioning_lambda_function_name = (
            f"{VPConstants.APP_NAME}-pre-provisioning-lambda"
        )

        post_provisioning_lambda_function_name = (
            f"{VPConstants.APP_NAME}-post-provisioning-lambda"
        )

        initial_connection_lambda_function_name = (
            f"{VPConstants.APP_NAME}-initial-connection-lambda"
        )

        # Create Lambda roles and policies
        pre_provisioning_hook_lambda_role = aws_iam.Role(
            self,
            "pre-provision-hook-lambda-role",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            path="/",
            inline_policies={
                "iot-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=["iot:UpdateCertificate", "iot:DeleteCertificate"],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="iot",
                                    resource="cert",
                                    resource_name="*",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                            ],
                        )
                    ]
                ),
                "cloudwatch-logs-policy": generate_lambda_cloudwatch_logs_policy_document(
                    self, lambda_function_name=pre_provisioning_lambda_function_name
                ),
                "dynamodb-provisioned-vehicles-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "dynamodb:Query",
                                "dynamodb:PutItem",
                                "dynamodb:UpdateItem",
                            ],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="dynamodb",
                                    resource="table",
                                    resource_name=f"{self.provisioned_vehicles_table.table_name}",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                            ],
                        ),
                        generate_kms_policy_statement(
                            self,
                            kms_encryption_key_id=self.provisioned_vehicles_table_kms_key.key_id,
                            allow_encrypt=True,
                        ),
                    ]
                ),
                "dynamodb-authorized-vehicles-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "dynamodb:GetItem",
                            ],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="dynamodb",
                                    resource="table",
                                    resource_name=f"{self.authorized_vehicles_table.table_name}",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                            ],
                        ),
                        generate_kms_policy_statement(
                            self,
                            kms_encryption_key_id=self.authorized_vehicles_table_kms_key.key_id,
                            allow_encrypt=False,
                        ),
                    ]
                ),
            },
        )

        post_provisioning_hook_lambda_role = aws_iam.Role(
            self,
            "post-provision-hook-lambda-role",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            path="/",
            inline_policies={
                "iot-policy": aws_iam.PolicyDocument(
                    statements=[
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
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "iot:ListAttachedPolicies",
                                "iot:ListCertificates",
                                "iot:DetachThingPrincipal",
                            ],
                            resources=[
                                "*"
                            ],  # These actions require a wildcard resource
                        ),
                    ]
                ),
                "cloudwatch-logs-policy": generate_lambda_cloudwatch_logs_policy_document(
                    self, lambda_function_name=post_provisioning_lambda_function_name
                ),
                "dynamodb-provisioned-vehicles-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "dynamodb:Query",
                                "dynamodb:UpdateItem",
                            ],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="dynamodb",
                                    resource="table",
                                    resource_name=f"{self.provisioned_vehicles_table.table_name}",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                            ],
                        ),
                        generate_kms_policy_statement(
                            self,
                            kms_encryption_key_id=self.provisioned_vehicles_table_kms_key.key_id,
                            allow_encrypt=True,
                        ),
                    ]
                ),
            },
        )

        initial_connection_lambda_role = aws_iam.Role(
            self,
            "initial-connection-lambda-role",
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
                                    resource_name=f"{self.provisioned_vehicles_table.table_name}",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                            ],
                        ),
                        generate_kms_policy_statement(
                            self,
                            kms_encryption_key_id=self.provisioned_vehicles_table_kms_key.key_id,
                            allow_encrypt=True,
                        ),
                    ]
                ),
            },
        )

        # Lambda function which will act as our pre-provisioning hook
        pre_provisioning_lambda_function = aws_lambda.Function(
            self,
            "pre-provisioning-hook-lambda",
            function_name=pre_provisioning_lambda_function_name,
            code=aws_lambda.Code.from_asset("source/handlers"),
            description="Vehicle Provisioning Pre-Provisioning Hook",
            handler="provisioning.pre_provision.handler",
            runtime=aws_lambda.Runtime.PYTHON_3_10,
            role=pre_provisioning_hook_lambda_role,
            layers=[
                aws_lambda.LayerVersion.from_layer_version_arn(
                    self,
                    "pre-provisioning-lambda-dependency-layer-version",
                    aws_ssm.StringParameter.from_string_parameter_name(
                        self,
                        "pre-provisioning-dependency-layer-arn",
                        f"/{VPConstants.STAGE}/{VPConstants.APP_NAME}/arns/dependency-layer-arn",
                    ).string_value,
                )
            ],
            timeout=Duration.minutes(1),
            environment={
                DynamoTableNameKey.AUTHORIZED_VEHICLES_TABLE_NAME.value: self.authorized_vehicles_table.table_name,
                DynamoTableNameKey.PROVISIONED_VEHICLES_TABLE_NAME.value: self.provisioned_vehicles_table.table_name,
                "USER_AGENT_STRING": VPConstants.USER_AGENT_STRING,
            },
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
        )

        # Lambda function which will trigger post-provisioning
        post_provisioning_lambda_function = aws_lambda.Function(
            self,
            "post-provisioning-hook-lambda",
            function_name=post_provisioning_lambda_function_name,
            code=aws_lambda.Code.from_asset("source/handlers"),
            description="Vehicle Provisioning Post-Provisioning Function",
            handler="provisioning.post_provision.handler",
            runtime=aws_lambda.Runtime.PYTHON_3_10,
            role=post_provisioning_hook_lambda_role,
            layers=[
                aws_lambda.LayerVersion.from_layer_version_arn(
                    self,
                    "post-provisioning-lambda-dependency-layer-version",
                    aws_ssm.StringParameter.from_string_parameter_name(
                        self,
                        "post-provisioning-lambda-dependency-layer-arn",
                        f"/{VPConstants.STAGE}/{VPConstants.APP_NAME}/arns/dependency-layer-arn",
                    ).string_value,
                )
            ],
            timeout=Duration.minutes(1),
            environment={
                DynamoTableNameKey.PROVISIONED_VEHICLES_TABLE_NAME.value: self.provisioned_vehicles_table.table_name,
                "PROVISIONING_TEMPLATE_NAME": VPConstants.PROVISIONING_TEMPLATE_NAME,
                "USER_AGENT_STRING": VPConstants.USER_AGENT_STRING,
            },
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
        )

        # Lambda function which will trigger on vehicle connection
        initial_connection_lambda_function = aws_lambda.Function(
            self,
            "initial-connection-lambda",
            function_name=initial_connection_lambda_function_name,
            code=aws_lambda.Code.from_asset("source/handlers"),
            description="Vehicle Provisioning Initial Connection Function",
            handler="provisioning.initial_connection.handler",
            runtime=aws_lambda.Runtime.PYTHON_3_10,
            role=initial_connection_lambda_role,
            layers=[
                aws_lambda.LayerVersion.from_layer_version_arn(
                    self,
                    "initial-connection-lambda-dependency-layer-version",
                    aws_ssm.StringParameter.from_string_parameter_name(
                        self,
                        "initial-connectioon-lambda-dependency-layer-arn",
                        f"/{VPConstants.STAGE}/{VPConstants.APP_NAME}/arns/dependency-layer-arn",
                    ).string_value,
                )
            ],
            timeout=Duration.minutes(1),
            environment={
                DynamoTableNameKey.PROVISIONED_VEHICLES_TABLE_NAME.value: self.provisioned_vehicles_table.table_name,
                "USER_AGENT_STRING": VPConstants.USER_AGENT_STRING,
            },
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
        )

        # Add permission for IoT to invoke our lambda functions to the lambda function's resource based policies
        pre_provisioning_lambda_function.add_permission(
            id="iot-invoke-pre-provisioning-lambda-permission",
            principal=aws_iam.ServicePrincipal("iot.amazonaws.com"),
            action="lambda:InvokeFunction",
            source_account=str(self.account),
        )

        post_provisioning_lambda_function.add_permission(
            id="iot-invoke-post-provisioning-lambda-permission",
            principal=aws_iam.ServicePrincipal("iot.amazonaws.com"),
            action="lambda:InvokeFunction",
            source_account=str(self.account),
        )

        initial_connection_lambda_function.add_permission(
            id="iot-invoke-initial-connection-lambda-permission",
            principal=aws_iam.ServicePrincipal("iot.amazonaws.com"),
            action="lambda:InvokeFunction",
            source_account=str(self.account),
        )

        lambda_functions = ProvisioningLambdaFunctions(
            pre_provisioning_lambda=pre_provisioning_lambda_function,
            post_provisioning_lambda=post_provisioning_lambda_function,
            initial_connection_lambda=initial_connection_lambda_function,
        )
        return lambda_functions

    def setup_iot_core_rules(self) -> Tuple[aws_iot.CfnTopicRule, aws_iot.CfnTopicRule]:
        thing_event_topic_rule = aws_iot.CfnTopicRule(
            self,
            "iot-post-provisioning-lambda-rule",
            rule_name="iot_post_provisioning_lambda_rule",  # IoT Rules follow a regex pattern that does not allow kebab case: ^[a-zA-Z0-9_]+$
            topic_rule_payload=aws_iot.CfnTopicRule.TopicRulePayloadProperty(
                sql="SELECT * FROM '$aws/events/thing/+/+'",
                description="Trigger lambda to insert ProvisionedVehicles record on successful thing creation or update (triggered by RegisterThing).",
                actions=[
                    aws_iot.CfnTopicRule.ActionProperty(
                        lambda_=aws_iot.CfnTopicRule.LambdaActionProperty(
                            function_arn=self.post_provisioning_lambda.function_arn
                        )
                    )
                ],
            ),
        )

        initial_connection_topic_rule = aws_iot.CfnTopicRule(
            self,
            "iot-initial-connection-lambda-rule",
            rule_name="iot_initial_connection_lambda_rule",  # IoT Rules follow a regex pattern that does not allow kebab case: ^[a-zA-Z0-9_]+$
            topic_rule_payload=aws_iot.CfnTopicRule.TopicRulePayloadProperty(
                sql="SELECT * FROM 'vehicleactive/#'",
                description="Trigger lambda to updated ProvisionedVehicles record on vehicle initial connection.",
                actions=[
                    aws_iot.CfnTopicRule.ActionProperty(
                        lambda_=aws_iot.CfnTopicRule.LambdaActionProperty(
                            function_arn=self.initial_connection_lambda.function_arn
                        )
                    )
                ],
            ),
        )
        return thing_event_topic_rule, initial_connection_topic_rule
