# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# AWS Libraries
from aws_cdk import CustomResource, aws_iam
from constructs import Construct

# CMS Common Library
from cms_common.constructs.custom_resource_lambda import CustomResourceLambdaConstruct

# Connected Mobility Solution on AWS
from ...handlers.custom_resource.function.lib.custom_resource_type_enum import (
    CustomResourceType,
)
from .grafana_api_key import GrafanaApiKeyConstruct


class GrafanaPluginsConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        grafana_workspace_endpoint: str,
        grafana_api_key_construct: GrafanaApiKeyConstruct,
        custom_resource_lambda_construct: CustomResourceLambdaConstruct,
    ) -> None:
        super().__init__(scope, construct_id)

        install_plugin_custom_resource_policy = aws_iam.Policy(
            self,
            "custom-resource-policy",
            statements=[
                aws_iam.PolicyStatement(
                    actions=[
                        "secretsmanager:GetSecretValue",
                    ],
                    effect=aws_iam.Effect.ALLOW,
                    resources=[
                        grafana_api_key_construct.secret.secret_arn,
                    ],
                ),
            ],
        )
        custom_resource_lambda_construct.add_policy_to_custom_resource_lambda(
            policy=install_plugin_custom_resource_policy
        )

        install_athena_plugin_custom_resource = CustomResource(
            self,
            "install-athena-plugin-custom-resource",
            service_token=custom_resource_lambda_construct.function.function_arn,
            resource_type=f"Custom::{CustomResourceType.ResourceType.INSTALL_GRAFANA_PLUGIN.value}",
            properties={
                "Resource": CustomResourceType.ResourceType.INSTALL_GRAFANA_PLUGIN.value,
                "GrafanaWorkspaceEndpoint": grafana_workspace_endpoint,
                "GrafanaApiKeySecretArn": grafana_api_key_construct.secret.secret_arn,
                "PluginName": "grafana-athena-datasource",
            },
        )
        install_athena_plugin_custom_resource.node.add_dependency(
            grafana_api_key_construct
        )
