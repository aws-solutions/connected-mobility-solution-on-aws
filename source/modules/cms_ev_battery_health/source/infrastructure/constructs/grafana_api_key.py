# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library

# AWS Libraries
from aws_cdk import (
    ArnFormat,
    CustomResource,
    Duration,
    RemovalPolicy,
    Stack,
    aws_ec2,
    aws_iam,
    aws_lambda,
    aws_logs,
    aws_secretsmanager,
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

# Connected Mobility Solution on AWS
from ...handlers.custom_resource.function.lib.custom_resource_type_enum import (
    CustomResourceType,
)


class GrafanaApiKeyConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_unique_id: str,
        solution_config_inputs: SolutionConfigInputs,
        dependency_layer: aws_lambda.LayerVersion,
        grafana_workspace_endpoint: str,
        grafana_workspace_id: str,
        custom_resource_lambda_construct: CustomResourceLambdaConstruct,
        grafana_api_key_expiration_days: int,
        vpc_construct: VpcConstruct,
    ) -> None:
        super().__init__(scope, construct_id)

        api_key_secret_name = ResourceName.slash_separated(
            prefix=ResourcePrefix.slash_separated(
                app_unique_id=app_unique_id,
                module_name=solution_config_inputs.module_short_name,
            ),
            name="grafana-api-key",
        )

        self.secret = aws_secretsmanager.Secret(
            self,
            "secret",
            secret_name=api_key_secret_name,
            removal_policy=RemovalPolicy.DESTROY,
        )

        rotate_secret_lambda_function_name = ResourceName.hyphen_separated(
            prefix=ResourcePrefix.hyphen_separated(
                app_unique_id=app_unique_id,
                module_name=solution_config_inputs.module_short_name,
            ),
            name="rotate-secret",
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
                "ec2-vpc-policy": generate_ec2_vpc_policy(
                    self,
                    vpc_construct=vpc_construct,
                    subnet_selection=vpc_construct.private_subnet_selection,
                    authorized_service="lambda.amazonaws.com",
                ),
            },
        )

        self.rotate_secret_lambda = aws_lambda.Function(
            self,
            "rotate-secret-lambda-function",
            description="CMS EV battery health rotate secret lambda function",
            handler="function.main.handler",
            function_name=rotate_secret_lambda_function_name,
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            code=aws_lambda.Code.from_asset("deployment/dist/lambda/rotate_secret.zip"),
            timeout=Duration.seconds(60),
            role=rotate_secret_lambda_role,
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
                "GRAFANA_WORKSPACE_ENDPOINT": grafana_workspace_endpoint,
                "GRAFANA_API_KEY_EXPIRATION_DAYS": str(grafana_api_key_expiration_days),
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
            automatically_after=Duration.days(int(grafana_api_key_expiration_days) - 1),
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
            service_token=custom_resource_lambda_construct.function.function_arn,
            resource_type=f"Custom::{CustomResourceType.ResourceType.CREATE_GRAFANA_API_KEY.value}",
            properties={
                "Resource": CustomResourceType.ResourceType.CREATE_GRAFANA_API_KEY.value,
                "GrafanaWorkspaceId": grafana_workspace_id,
                "GrafanaApiKeySecretArn": self.secret.secret_arn,
                "GrafanaApiKeyExpirationDays": str(grafana_api_key_expiration_days),
            },
        )
        create_api_key_custom_resource.node.add_dependency(
            api_key_custom_resource_policy
        )
