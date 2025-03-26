# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# AWS Libraries
from aws_cdk import CustomResource, Stack, aws_iam
from constructs import Construct

# CMS Common Library
from cms_common.constructs.custom_resource_lambda import CustomResourceLambdaConstruct

# Connected Mobility Solution on AWS
from .cognito_app_client import CognitoAppClientConstruct
from .fleet_management_api import FleetManagementAPIConstruct
from .location_map import LocationMapConstruct
from .module_integration import ModuleInputsConstruct
from .user_interface_deployment import UserInterfaceDeploymentConstruct


class UserInterfaceConfigConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        module_inputs: ModuleInputsConstruct,
        custom_resource_lambda_construct: CustomResourceLambdaConstruct,
        cognito_app_client: CognitoAppClientConstruct,
        location_map: LocationMapConstruct,
        user_interface_deployment: UserInterfaceDeploymentConstruct,
        fleet_management_api: FleetManagementAPIConstruct,
    ) -> None:
        super().__init__(scope, construct_id)

        ui_bucket = user_interface_deployment.ui_bucket

        custom_resource_policy = aws_iam.Policy(
            self,
            "custom-resource-policy",
            statements=[
                aws_iam.PolicyStatement(
                    effect=aws_iam.Effect.ALLOW,
                    actions=["s3:PutObject", "s3:AbortMultipartUpload"],
                    resources=[
                        f"{ui_bucket.bucket.bucket_arn}/*",
                    ],
                ),
                aws_iam.PolicyStatement(
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "secretsmanager:GetSecretValue",
                    ],
                    resources=[module_inputs.cognito_config.idp_config_secret_arn],
                ),
            ],
        )
        custom_resource_lambda_construct.add_policy_to_custom_resource_lambda(
            policy=custom_resource_policy
        )
        custom_resources_lambda_function_arn = (
            custom_resource_lambda_construct.function.function_arn
        )

        scope_names = " ".join(
            scope.scope_name for scope in cognito_app_client.supported_scopes
        )

        config_file_name = "runtimeConfig.json"
        self.s3_config_path = f"s3://{ui_bucket.bucket.bucket_name}{user_interface_deployment.ui_bucket_prefix}{config_file_name}"

        runtime_config_custom_resource = CustomResource(
            self,
            "runtime-config",
            service_token=custom_resources_lambda_function_arn,
            resource_type="Custom::CopyConfigFiles",
            properties={
                "Resource": "CreateConfig",
                "ConfigFileName": config_file_name,
                "DestinationBucket": ui_bucket.bucket.bucket_name,
                "DestinationKeyPrefix": user_interface_deployment.ui_bucket_prefix,
                "idpConfigSecretArn": module_inputs.cognito_config.idp_config_secret_arn,
                "configBase": {
                    "awsRegion": Stack.of(self).region,
                    "isDemoMode": module_inputs.is_demo_mode,
                    "apiEndpoint": fleet_management_api.api.url,
                    "oAuth": {
                        "clientId": cognito_app_client.cms_ui_client_id,
                        "scopes": scope_names,
                    },
                    "mapAuth": {
                        "mapName": location_map.map_name,
                        "identityPoolId": location_map.identity_pool.ref,
                        "identityPoolClient": f"cognito-idp.{Stack.of(self).region}.amazonaws.com/{module_inputs.cognito_config.cognito_user_pool_id}",
                    },
                },
            },
        )

        runtime_config_custom_resource.node.add_dependency(
            custom_resource_policy, user_interface_deployment.ui_deployment
        )
