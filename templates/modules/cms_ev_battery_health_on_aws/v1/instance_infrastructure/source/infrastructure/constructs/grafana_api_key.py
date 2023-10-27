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
    aws_lambda,
    aws_logs,
    aws_secretsmanager,
)
from constructs import Construct

# Connected Mobility Solution on AWS
from ...config.constants import EVBatteryHealthConstants
from ...handlers.custom_resource.lib.custom_resource_type_enum import CustomResourceType
from ..lib.policy_generators import generate_lambda_cloudwatch_logs_policy_document
from .custom_resource_lambda import CustomResourceLambdaConstruct


class GrafanaApiKeyConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        dependency_layer: aws_lambda.LayerVersion,
        grafana_workspace_endpoint: str,
        grafana_workspace_id: str,
        custom_resource_lambda_construct: CustomResourceLambdaConstruct,
    ) -> None:
        super().__init__(scope, construct_id)

        api_key_secret_name = f"{EVBatteryHealthConstants.STAGE}/{EVBatteryHealthConstants.APP_NAME}/grafana-api-key"

        self.secret = aws_secretsmanager.Secret(
            self,
            "secret",
            secret_name=api_key_secret_name,
            removal_policy=RemovalPolicy.DESTROY,
        )

        rotate_secret_lambda_function_name = (
            f"{EVBatteryHealthConstants.APP_NAME}-rotate-secret-lambda"
        )

        rotate_secret_lambda_role = aws_iam.Role(
            self,
            "rotate-secret-lambda-role",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            inline_policies={
                "secrets-manager-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            actions=[
                                "secretsmanager:GetSecretValue",
                                "secretsmanager:PutSecretValue",
                                "secretsmanager:DescribeSecret",
                                "secretsmanager:UpdateSecretVersionStage",
                            ],
                            effect=aws_iam.Effect.ALLOW,
                            resources=[
                                Stack.of(self).format_arn(
                                    service="secretsmanager",
                                    resource="secret",
                                    resource_name=api_key_secret_name,
                                    arn_format=ArnFormat.COLON_RESOURCE_NAME,
                                ),
                            ],
                        ),
                    ]
                ),
                "grafana-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            actions=[
                                "grafana:CreateWorkspaceApiKey",
                                "grafana:DeleteWorkspaceApiKey",
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
                    self, lambda_function_name=rotate_secret_lambda_function_name
                ),
            },
        )

        self.rotate_secret_lambda = aws_lambda.Function(
            self,
            "rotate-secret-lambda-function",
            description="CMS EV battery health rotate secret lambda function",
            handler="rotate_secret.main.handler",
            function_name=rotate_secret_lambda_function_name,
            runtime=aws_lambda.Runtime.PYTHON_3_10,
            code=aws_lambda.Code.from_asset("source/handlers"),
            timeout=Duration.seconds(60),
            role=rotate_secret_lambda_role,
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
            layers=[dependency_layer],
            environment={
                "USER_AGENT_STRING": EVBatteryHealthConstants.USER_AGENT_STRING,
                "GRAFANA_WORKSPACE_ENDPOINT": grafana_workspace_endpoint,
                "GRAFANA_API_KEY_EXPIRATION_DAYS": str(
                    EVBatteryHealthConstants.GRAFANA_API_KEY_EXPIRATION_DAYS
                ),
            },
        )

        self.rotate_secret_lambda.add_permission(
            id="secrets-manager-invoke-rotate-secret-lambda-permission",
            principal=aws_iam.ServicePrincipal("secretsmanager.amazonaws.com"),
            action="lambda:InvokeFunction",
            source_account=Stack.of(self).account,
        )

        aws_secretsmanager.RotationSchedule(
            self,
            "api-key-rotation-schedule",
            secret=self.secret,
            automatically_after=Duration.days(
                EVBatteryHealthConstants.GRAFANA_API_KEY_EXPIRATION_DAYS - 1
            ),
            rotate_immediately_on_update=False,
            rotation_lambda=self.rotate_secret_lambda,
        )

        api_key_custom_resource_policy = aws_iam.Policy(
            self,
            "custom-resource-policy",
            statements=[
                aws_iam.PolicyStatement(
                    actions=[
                        "secretsmanager:PutSecretValue",
                    ],
                    effect=aws_iam.Effect.ALLOW,
                    resources=[
                        self.secret.secret_arn,
                    ],
                ),
                aws_iam.PolicyStatement(
                    actions=[
                        "grafana:CreateWorkspaceApiKey",
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
        custom_resource_lambda_construct.add_policy_to_custom_resource_lambda(
            policy=api_key_custom_resource_policy
        )

        create_api_key_custom_resource = CustomResource(
            self,
            "create-grafana-api-key-custom-resource",
            service_token=custom_resource_lambda_construct.custom_resource_lambda.function_arn,
            resource_type=f"Custom::{CustomResourceType.ResourceType.CREATE_GRAFANA_API_KEY.value}",
            properties={
                "Resource": CustomResourceType.ResourceType.CREATE_GRAFANA_API_KEY.value,
                "GrafanaWorkspaceId": grafana_workspace_id,
                "GrafanaApiKeySecretArn": self.secret.secret_arn,
                "GrafanaApiKeyExpirationDays": str(
                    EVBatteryHealthConstants.GRAFANA_API_KEY_EXPIRATION_DAYS
                ),
            },
        )
        create_api_key_custom_resource.node.add_dependency(
            api_key_custom_resource_policy
        )
