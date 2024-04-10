# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# AWS Libraries
from aws_cdk import (
    ArnFormat,
    CustomResource,
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
from cms_common.constructs.custom_resource_lambda import CustomResourceLambdaConstruct
from cms_common.constructs.vpc_construct import VpcConstruct
from cms_common.policy_generators.cloudwatch import (
    generate_lambda_cloudwatch_logs_policy_document,
)
from cms_common.policy_generators.ec2_vpc import generate_ec2_vpc_policy
from cms_common.policy_generators.kms import generate_kms_policy_statement

# Connected Mobility Solution on AWS
from ...handlers.custom_resource.function.lib.custom_resource_type_enum import (
    CustomResourceFunctionType,
)
from ...handlers.provisioning.function.lib.dynamo_table_name_key_enum import (
    DynamoTableNameKey,
)
from .provisioning_database import ProvisioningDBResources


class PostProvisioningConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_unique_id: str,
        solution_config_inputs: SolutionConfigInputs,
        dependency_layer: aws_lambda.LayerVersion,
        custom_resource_lambda_construct: CustomResourceLambdaConstruct,
        provisioning_db_resources: ProvisioningDBResources,
        provisioning_template_name: str,
        vpc_construct: VpcConstruct,
    ) -> None:
        super().__init__(scope, construct_id)

        post_provisioning_custom_resource_policy = aws_iam.Policy(
            self,
            "custom-resource-policy",
            statements=[
                aws_iam.PolicyStatement(
                    actions=[
                        "iot:UpdateEventConfigurations",
                    ],
                    effect=aws_iam.Effect.ALLOW,
                    resources=["*"],
                ),
            ],
        )
        custom_resource_lambda_construct.add_policy_to_custom_resource_lambda(
            policy=post_provisioning_custom_resource_policy,
        )

        update_event_configuration = CustomResource(
            self,
            "update-event-configurations",
            service_token=custom_resource_lambda_construct.function.function_arn,
            resource_type=f"Custom::{CustomResourceFunctionType.UPDATE_EVENT_CONFIGURATIONS.value}",
            properties={
                "Resource": CustomResourceFunctionType.UPDATE_EVENT_CONFIGURATIONS.value
            },
        )
        update_event_configuration.node.add_dependency(
            post_provisioning_custom_resource_policy
        )

        post_provisioning_lambda_function_name = ResourceName.hyphen_separated(
            prefix=ResourcePrefix.hyphen_separated(
                app_unique_id=app_unique_id,
                module_name=solution_config_inputs.module_short_name,
            ),
            name="post-provisioning",
        )

        post_provisioning_hook_lambda_role = aws_iam.Role(
            self,
            "lambda-role",
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

        # Lambda function which will trigger post-provisioning
        post_provisioning_lambda_function = aws_lambda.Function(
            self,
            "lambda-function",
            function_name=post_provisioning_lambda_function_name,
            code=aws_lambda.Code.from_asset("dist/lambda/provisioning.zip"),
            description="CMS Provisioning post-provisioning lambda function",
            handler="function.post_provision.handler",
            runtime=aws_lambda.Runtime.PYTHON_3_10,
            role=post_provisioning_hook_lambda_role,
            layers=[dependency_layer],
            timeout=Duration.minutes(1),
            environment={
                DynamoTableNameKey.PROVISIONED_VEHICLES_TABLE_NAME.value: provisioning_db_resources.provisioned_vehicles_table.table_name,
                "PROVISIONING_TEMPLATE_NAME": provisioning_template_name,
                "USER_AGENT_STRING": solution_config_inputs.get_user_agent_string(),
            },
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

        post_provisioning_lambda_function.add_permission(
            id="iot-invoke-post-provisioning-lambda-permission",
            principal=aws_iam.ServicePrincipal("iot.amazonaws.com"),
            action="lambda:InvokeFunction",
            source_account=Stack.of(self).account,
        )

        aws_iot.CfnTopicRule(
            self,
            "iot-post-provisioning-lambda-rule",
            rule_name=ResourceName.underscore_separated(
                prefix=ResourcePrefix.only_underscore_separated(
                    app_unique_id=app_unique_id,
                    module_name=solution_config_inputs.module_short_name,
                ),
                name="iot_post_provisioning",
            ),
            topic_rule_payload=aws_iot.CfnTopicRule.TopicRulePayloadProperty(
                sql="SELECT * FROM '$aws/events/thing/+/+'",
                description="Trigger lambda to insert ProvisionedVehicles record on successful thing creation or update (triggered by RegisterThing).",
                actions=[
                    aws_iot.CfnTopicRule.ActionProperty(
                        lambda_=aws_iot.CfnTopicRule.LambdaActionProperty(
                            function_arn=post_provisioning_lambda_function.function_arn,
                        )
                    )
                ],
            ),
        )
