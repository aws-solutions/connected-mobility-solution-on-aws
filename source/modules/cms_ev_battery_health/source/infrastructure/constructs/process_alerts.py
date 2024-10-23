# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# AWS Libraries
from aws_cdk import (
    ArnFormat,
    CustomResource,
    Duration,
    RemovalPolicy,
    Stack,
    aws_ec2,
    aws_iam,
    aws_kms,
    aws_lambda,
    aws_lambda_event_sources,
    aws_logs,
    aws_sns,
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
from cms_common.constructs.custom_resource_lambda import CustomResourceLambdaConstruct
from cms_common.constructs.vpc_construct import VpcConstruct
from cms_common.policy_generators.cloudwatch import (
    generate_lambda_cloudwatch_logs_policy_document,
)
from cms_common.policy_generators.ec2_vpc import generate_ec2_vpc_policy
from cms_common.resource_names.auth import AuthSetupResourceNames

# Connected Mobility Solution on AWS
from ...handlers.custom_resource.function.lib.custom_resource_type_enum import (
    CustomResourceType,
)
from ..constructs.grafana_workspace import GrafanaWorkspaceConstruct


class ProcessAlertsConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_unique_id: str,
        solution_config_inputs: SolutionConfigInputs,
        dependency_layer: aws_lambda.LayerVersion,
        grafana_api_key_secret_arn: str,
        grafana_workspace_construct: GrafanaWorkspaceConstruct,
        custom_resource_lambda_construct: CustomResourceLambdaConstruct,
        identity_provider_id: str,
        alerts_publish_endpoint_url: str,
        vpc_construct: VpcConstruct,
    ) -> None:
        super().__init__(scope, construct_id)

        auth_setup_resource_names = AuthSetupResourceNames.from_identity_provider_id(
            identity_provider_id
        )

        alert_contact_point_sns_topic_encryption_key = aws_kms.Key(
            self,
            "alert-contact-point-sns-topic-encryption-key",
            enable_key_rotation=True,
            removal_policy=RemovalPolicy.DESTROY,
        )

        topic_name = ResourceName.hyphen_separated(
            prefix=ResourcePrefix.hyphen_separated(
                app_unique_id=app_unique_id,
                module_name=solution_config_inputs.module_short_name,
            ),
            name="grafana-alerts",
        )
        self.alert_contact_point_sns_topic = aws_sns.Topic(
            self,
            "alert-contact-point-sns-topic",
            topic_name=topic_name,
            master_key=alert_contact_point_sns_topic_encryption_key,
        )

        process_alerts_grafana_workspace_policy = aws_iam.Policy(
            self,
            "grafana-workspace-policy",
            statements=[
                aws_iam.PolicyStatement(
                    actions=[
                        "sns:Publish",
                        "sns:GetTopicAttributes",
                        "sns:ListTagsForResource",
                    ],
                    effect=aws_iam.Effect.ALLOW,
                    resources=[
                        Stack.of(self).format_arn(
                            service="sns",
                            resource=topic_name,
                            arn_format=ArnFormat.COLON_RESOURCE_NAME,
                        ),
                    ],
                ),
                aws_iam.PolicyStatement(
                    effect=aws_iam.Effect.ALLOW,
                    actions=["kms:Decrypt", "kms:GenerateDataKey"],
                    resources=[
                        alert_contact_point_sns_topic_encryption_key.key_arn,
                    ],
                ),
            ],
        )

        grafana_workspace_construct.add_policy_to_grafana_workspace(
            policy=process_alerts_grafana_workspace_policy,
        )

        process_alerts_lambda_name = ResourceName.hyphen_separated(
            prefix=ResourcePrefix.hyphen_separated(
                app_unique_id=app_unique_id,
                module_name=solution_config_inputs.module_short_name,
            ),
            name="process-alerts",
        )

        process_alerts_lambda_role = aws_iam.Role(
            self,
            "lambda-role",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            inline_policies={
                "cloudwatch-policy": generate_lambda_cloudwatch_logs_policy_document(
                    self, lambda_function_name=process_alerts_lambda_name
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
                                    auth_setup_resource_names.service_client_config_secret_arn_ssm_parameter
                                ),
                                resolve_ssm_parameter(
                                    auth_setup_resource_names.idp_config_secret_arn_ssm_parameter
                                ),
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
                                    resource_name=remove_leading_slash(
                                        auth_setup_resource_names.service_client_config_secret_arn_ssm_parameter
                                    ),  # Leading slash must not be present on SSM IAM permissions
                                ),
                                Stack.of(self).format_arn(
                                    service="ssm",
                                    resource="parameter",
                                    resource_name=remove_leading_slash(
                                        auth_setup_resource_names.idp_config_secret_arn_ssm_parameter
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

        process_alerts_lambda = aws_lambda.Function(
            self,
            "lambda-function",
            description="CMS EV Battery Health process alerts lambda.",
            handler="function.main.handler",
            function_name=process_alerts_lambda_name,
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            code=aws_lambda.Code.from_asset("dist/lambda/process_alerts.zip"),
            timeout=Duration.seconds(60),
            role=process_alerts_lambda_role,
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
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
            environment={
                "USER_AGENT_STRING": solution_config_inputs.get_user_agent_string(),
                "IDENTITY_PROVIDER_ID": identity_provider_id,
                "ALERTS_PUBLISH_ENDPOINT_URL": alerts_publish_endpoint_url,
            },
        )

        process_alerts_lambda_sns_source = aws_lambda_event_sources.SnsEventSource(
            topic=self.alert_contact_point_sns_topic,
        )

        process_alerts_lambda.add_event_source(process_alerts_lambda_sns_source)

        process_alerts_custom_resource_policy = aws_iam.Policy(
            self,
            "custom-resource-policy",
            statements=[
                aws_iam.PolicyStatement(
                    actions=[
                        "secretsmanager:GetSecretValue",
                    ],
                    effect=aws_iam.Effect.ALLOW,
                    resources=[
                        grafana_api_key_secret_arn,
                    ],
                ),
            ],
        )
        custom_resource_lambda_construct.add_policy_to_custom_resource_lambda(
            policy=process_alerts_custom_resource_policy
        )

        set_alert_configuration_custom_resource = CustomResource(
            self,
            "set-grafana-alert-configuration-custom-resource",
            service_token=custom_resource_lambda_construct.function.function_arn,
            resource_type=f"Custom::{CustomResourceType.ResourceType.SET_GRAFANA_ALERT_CONFIGURATION.value}",
            properties={
                "Resource": CustomResourceType.ResourceType.SET_GRAFANA_ALERT_CONFIGURATION.value,
                "GrafanaApiKeySecretArn": grafana_api_key_secret_arn,
                "GrafanaWorkspaceEndpoint": grafana_workspace_construct.workspace.attr_endpoint,
                "GrafanaAlertsSnsTopicArn": self.alert_contact_point_sns_topic.topic_arn,
            },
        )
        set_alert_configuration_custom_resource.node.add_dependency(
            process_alerts_custom_resource_policy
        )
