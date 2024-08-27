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
    aws_lambda,
    aws_logs,
    custom_resources,
)
from constructs import Construct

# CMS Common Library
from cms_common.config.resource_names import ResourceName, ResourcePrefix
from cms_common.config.stack_inputs import SolutionConfigInputs
from cms_common.constructs.custom_resource_lambda import CustomResourceLambdaConstruct
from cms_common.constructs.vpc_construct import VpcConstruct
from cms_common.policy_generators.ec2_vpc import generate_ec2_vpc_policy

# Connected Mobility Solution on AWS
from ...handlers.custom_resource.function.lib.custom_resource_type_enum import (
    CustomResourceType,
)
from ..lib.policy_generators import generate_lambda_cloudwatch_logs_policy_document


class ProvisionAlertsConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_unique_id: str,
        solution_config_inputs: SolutionConfigInputs,
        dependency_layer: aws_lambda.LayerVersion,
        custom_resource_lambda_construct: CustomResourceLambdaConstruct,
        grafana_workspace_id: str,
        vpc_construct: VpcConstruct,
    ) -> None:
        super().__init__(scope, construct_id)

        check_workspace_active_lambda_name = ResourceName.hyphen_separated(
            prefix=ResourcePrefix.hyphen_separated(
                app_unique_id=app_unique_id,
                module_name=solution_config_inputs.module_short_name,
            ),
            name="workspace-active",
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
                "ec2-vpc-policy": generate_ec2_vpc_policy(
                    self,
                    vpc_construct=vpc_construct,
                    subnet_selection=vpc_construct.private_subnet_selection,
                    authorized_service="lambda.amazonaws.com",
                ),
            },
        )

        check_workspace_active_lambda = aws_lambda.Function(
            self,
            "check-workspace-active-lambda-function",
            description="Lambda that checks if grafana workspace is active.",
            handler="main.handler",
            function_name=check_workspace_active_lambda_name,
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            code=aws_lambda.Code.from_asset("dist/lambda/check_workspace_active.zip"),
            timeout=Duration.seconds(60),
            role=check_workspace_active_lambda_role,
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
            layers=[dependency_layer],
            vpc=vpc_construct.vpc,
            vpc_subnets=vpc_construct.private_subnet_selection,
            security_groups=[
                aws_ec2.SecurityGroup(
                    self,
                    "security-group-1",
                    vpc=vpc_construct.vpc,
                    allow_all_outbound=True,  # NOSONAR
                )
            ],
            environment={
                "USER_AGENT_STRING": solution_config_inputs.get_user_agent_string(),
                "GRAFANA_WORKSPACE_ID": grafana_workspace_id,
            },
        )

        custom_resource_provider = custom_resources.Provider(
            self,
            "custom-resource-provider",
            on_event_handler=custom_resource_lambda_construct.function,
            is_complete_handler=check_workspace_active_lambda,
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
            provider_function_name=ResourceName.hyphen_separated(
                prefix=ResourcePrefix.hyphen_separated(
                    app_unique_id=app_unique_id,
                    module_name=solution_config_inputs.module_short_name,
                ),
                name="provision-alerts",
            ),
            vpc=vpc_construct.vpc,
            vpc_subnets=vpc_construct.private_subnet_selection,
            security_groups=[
                aws_ec2.SecurityGroup(
                    self,
                    "security-group-2",
                    vpc=vpc_construct.vpc,
                    allow_all_outbound=True,  # NOSONAR
                )
            ],
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
