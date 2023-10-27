# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
from aws_cdk import (
    ArnFormat,
    CustomResource,
    Duration,
    RemovalPolicy,
    Stack,
    aws_iam,
    aws_kms,
    aws_lambda,
    aws_lambda_event_sources,
    aws_logs,
    aws_sns,
)
from constructs import Construct

# Connected Mobility Solution on AWS
from ...config.constants import EVBatteryHealthConstants
from ...handlers.custom_resource.lib.custom_resource_type_enum import CustomResourceType
from ..constructs.grafana_workspace import GrafanaWorkspaceConstruct
from ..lib.policy_generators import generate_lambda_cloudwatch_logs_policy_document
from .custom_resource_lambda import CustomResourceLambdaConstruct
from .module_integration import ServiceAuthenticationParameters


class ProcessAlertsConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        dependency_layer: aws_lambda.LayerVersion,
        grafana_api_key_secret_arn: str,
        grafana_workspace_construct: GrafanaWorkspaceConstruct,
        custom_resource_lambda_construct: CustomResourceLambdaConstruct,
        service_authentication_parameters: ServiceAuthenticationParameters,
        alerts_publish_endpoint_url: str,
    ) -> None:
        super().__init__(scope, construct_id)

        alert_contact_point_sns_topic_encryption_key = aws_kms.Key(
            self,
            "alert-contact-point-sns-topic-encryption-key",
            enable_key_rotation=True,
            removal_policy=RemovalPolicy.DESTROY,
        )

        self.alert_contact_point_sns_topic = aws_sns.Topic(
            self,
            "alert-contact-point-sns-topic",
            topic_name=f"grafana-alerts-{EVBatteryHealthConstants.APP_NAME}",
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
                            resource=EVBatteryHealthConstants.GRAFANA_ALERTS_SNS_TOPIC_NAME,
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

        process_alerts_lambda_name = (
            f"{EVBatteryHealthConstants.APP_NAME}-process-alerts-lambda"
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
                            actions=[
                                "secretsmanager:GetSecretValue",
                            ],
                            effect=aws_iam.Effect.ALLOW,
                            resources=[
                                service_authentication_parameters.client_secret_arn,
                            ],
                        ),
                    ]
                ),
            },
        )

        process_alerts_lambda = aws_lambda.Function(
            self,
            "lambda-function",
            description="CMS EV Battery Health process alerts lambda.",
            handler="process_alerts.main.handler",
            function_name=process_alerts_lambda_name,
            runtime=aws_lambda.Runtime.PYTHON_3_10,
            code=aws_lambda.Code.from_asset("source/handlers"),
            timeout=Duration.seconds(60),
            role=process_alerts_lambda_role,
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
            layers=[dependency_layer],
            environment={
                "USER_AGENT_STRING": EVBatteryHealthConstants.USER_AGENT_STRING,
                "AUTHENTICATION_SERVICE_CLIENT_ID": service_authentication_parameters.client_id,
                "AUTHENTICATION_SERVICE_CLIENT_SECRET_ARN": service_authentication_parameters.client_secret_arn,
                "AUTHENTICATION_SERVICE_CALLER_SCOPE": service_authentication_parameters.caller_scope,
                "AUTHENTICATION_RESOURCE_SERVER_ID": service_authentication_parameters.resource_server_id,
                "AUTHENTICATION_USER_POOL_DOMAIN": service_authentication_parameters.user_pool_domain,
                "AUTHENTICATION_USER_POOL_REGION": service_authentication_parameters.user_pool_region,
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
            service_token=custom_resource_lambda_construct.custom_resource_lambda.function_arn,
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
