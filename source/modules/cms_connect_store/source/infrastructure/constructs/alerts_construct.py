# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

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
from cms_common.config.resource_names import (
    ResourceName,
    ResourcePrefix,
    remove_leading_slash,
)
from cms_common.config.ssm import resolve_ssm_parameter
from cms_common.config.stack_inputs import SolutionConfigInputs
from cms_common.constructs.vpc_construct import VpcConstruct
from cms_common.policy_generators.ec2_vpc import generate_ec2_vpc_policy
from cms_common.resource_names.auth import AuthResourceNames
from cms_common.resource_names.module_short_names import CMSModuleShortNames

# Connected Mobility Solution on AWS
from ..lib.policy_generators import generate_lambda_cloudwatch_logs_policy_document


class AlertsConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_unique_id: str,
        solution_config_inputs: SolutionConfigInputs,
        dependency_layer: aws_lambda.LayerVersion,
        alerts_publish_endpoint_url: str,
        vehicle_notifications_iot_core_query: str,
        identity_provider_id: str,
        vpc_construct: VpcConstruct,
    ) -> None:
        super().__init__(scope, construct_id)

        auth_resource_names = AuthResourceNames.from_identity_provider_id(
            identity_provider_id
        )

        vehicle_trigger_alarm_lambda_name = ResourceName.hyphen_separated(
            prefix=ResourcePrefix.hyphen_separated(
                app_unique_id=app_unique_id,
                module_name=solution_config_inputs.module_short_name,
            ),
            name="vehicle-alarm",
        )

        vehicle_trigger_alarm_lambda_role = aws_iam.Role(
            self,
            "lambda-role",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),  # NOSONAR
            path="/",
            inline_policies={
                "cloudwatch-logs-policy": generate_lambda_cloudwatch_logs_policy_document(
                    self, lambda_function_name=vehicle_trigger_alarm_lambda_name
                ),
                "secretsmanager-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "secretsmanager:GetSecretValue",
                            ],
                            resources=[
                                resolve_ssm_parameter(
                                    auth_resource_names.client_config_secret_arn_ssm_parameter
                                )
                            ],
                        )
                    ]
                ),
                "ssm-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=["ssm:GetParameters", "ssm:GetParameter"],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="ssm",
                                    resource="parameter",
                                    resource_name=ResourceName.slash_separated(
                                        prefix=ResourcePrefix.slash_separated(
                                            app_unique_id=app_unique_id,
                                            module_name=CMSModuleShortNames.ALERTS,
                                        ),
                                        name="publish-api/endpoint",
                                    ),
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                                Stack.of(self).format_arn(
                                    service="ssm",
                                    resource="parameter",
                                    resource_name=remove_leading_slash(
                                        auth_resource_names.client_config_secret_arn_ssm_parameter
                                    ),  # Leading slash must not be present on SSM IAM permissions
                                ),
                            ],
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

        vehicle_trigger_alarm_lambda_function = aws_lambda.Function(
            self,
            "lambda-function",
            function_name=vehicle_trigger_alarm_lambda_name,
            code=aws_lambda.Code.from_asset("dist/lambda/vehicle_trigger_alarm.zip"),
            description="Vehicle Trigger Alarm Function",
            handler="function.main.handler",
            runtime=aws_lambda.Runtime.PYTHON_3_10,
            role=vehicle_trigger_alarm_lambda_role,
            layers=[dependency_layer],
            timeout=Duration.minutes(1),
            environment={
                "USER_AGENT_STRING": solution_config_inputs.get_user_agent_string(),
                "IDENTITY_PROVIDER_ID": identity_provider_id,
                "ALERTS_PUBLISH_ENDPOINT_URL_PARAMETER": alerts_publish_endpoint_url,
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

        vehicle_trigger_alarm_lambda_function.add_permission(
            id="iot-invoke-vehicle-trigger-alarm-permission",
            principal=aws_iam.ServicePrincipal("iot.amazonaws.com"),  # NOSONAR
            action="lambda:InvokeFunction",
            source_account=Stack.of(self).account,
        )

        aws_iot.CfnTopicRule(
            self,
            "iot-send-to-alarm-lambda",
            rule_name=ResourceName.underscore_separated(
                prefix=ResourcePrefix.only_underscore_separated(
                    app_unique_id=app_unique_id,
                    module_name=solution_config_inputs.module_short_name,
                ),
                name="iot_send_to_alarm_lambda",
            ),
            topic_rule_payload=aws_iot.CfnTopicRule.TopicRulePayloadProperty(
                sql=vehicle_notifications_iot_core_query,
                description="Send payload to vehicle_trigger_alarm lambda",
                actions=[
                    aws_iot.CfnTopicRule.ActionProperty(
                        lambda_=aws_iot.CfnTopicRule.LambdaActionProperty(
                            function_arn=vehicle_trigger_alarm_lambda_function.function_arn,
                        )
                    ),
                ],
            ),
        )
