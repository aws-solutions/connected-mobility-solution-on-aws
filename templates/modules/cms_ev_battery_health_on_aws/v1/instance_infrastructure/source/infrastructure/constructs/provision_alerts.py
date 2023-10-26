# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
from aws_cdk import (
    ArnFormat,
    CustomResource,
    Duration,
    Stack,
    aws_iam,
    aws_lambda,
    aws_logs,
    custom_resources,
)
from constructs import Construct

# Connected Mobility Solution on AWS
from ...config.constants import EVBatteryHealthConstants
from ...handlers.custom_resource.lib.custom_resource_type_enum import CustomResourceType
from ..lib.policy_generators import generate_lambda_cloudwatch_logs_policy_document
from .custom_resource_lambda import CustomResourceLambdaConstruct


class ProvisionAlertsConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        dependency_layer: aws_lambda.LayerVersion,
        custom_resource_lambda_construct: CustomResourceLambdaConstruct,
        grafana_workspace_id: str,
    ) -> None:
        super().__init__(scope, construct_id)

        check_workspace_active_lambda_name = (
            f"{EVBatteryHealthConstants.APP_NAME}-workspace-active-lambda"
        )

        check_workspace_active_lambda_role = aws_iam.Role(
            self,
            "check-workspace-active-lambda-role",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            inline_policies={
                "grafana-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            actions=[
                                "grafana:DescribeWorkspace",
                            ],
                            effect=aws_iam.Effect.ALLOW,
                            resources=[
                                Stack.of(self).format_arn(
                                    service="grafana",
                                    resource="/workspaces",
                                    resource_name=f"{grafana_workspace_id}",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                            ],
                        ),
                    ]
                ),
                "cloudwatch-policy": generate_lambda_cloudwatch_logs_policy_document(
                    self, lambda_function_name=check_workspace_active_lambda_name
                ),
            },
        )

        check_workspace_active_lambda = aws_lambda.Function(
            self,
            "check-workspace-active-lambda-function",
            description="Lambda that checks if grafana workspace is active.",
            handler="check_workspace_active.main.handler",
            function_name=check_workspace_active_lambda_name,
            runtime=aws_lambda.Runtime.PYTHON_3_10,
            code=aws_lambda.Code.from_asset("source/handlers"),
            timeout=Duration.seconds(60),
            role=check_workspace_active_lambda_role,
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
            layers=[dependency_layer],
            environment={
                "USER_AGENT_STRING": EVBatteryHealthConstants.USER_AGENT_STRING,
                "GRAFANA_WORKSPACE_ID": grafana_workspace_id,
            },
        )

        custom_resource_provider = custom_resources.Provider(
            self,
            "custom-resource-provider",
            on_event_handler=custom_resource_lambda_construct.custom_resource_lambda,
            is_complete_handler=check_workspace_active_lambda,
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
            provider_function_name=f"alert-provision-custom-resource-provider-{EVBatteryHealthConstants.STAGE}",
        )

        custom_resource_lambda_construct.add_policy_to_custom_resource_lambda(
            policy=aws_iam.Policy(
                self,
                "custom-resource-policy",
                statements=[
                    aws_iam.PolicyStatement(
                        actions=[
                            "grafana:UpdateWorkspaceConfiguration",
                        ],
                        effect=aws_iam.Effect.ALLOW,
                        resources=[
                            Stack.of(self).format_arn(
                                service="grafana",
                                resource="/workspaces",
                                resource_name=f"{grafana_workspace_id}",
                                arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                            ),
                        ],
                    ),
                ],
            )
        )

        CustomResource(
            self,
            "enable-alerting-custom-resource-custom-resource",
            service_token=custom_resource_provider.service_token,
            resource_type=f"Custom::{CustomResourceType.ResourceType.ENABLE_GRAFANA_ALERTING.value}",
            properties={
                "Resource": CustomResourceType.ResourceType.ENABLE_GRAFANA_ALERTING.value,
                "GrafanaWorkspaceId": grafana_workspace_id,
                "DoNotSendCFResponse": "True",
            },
        )
