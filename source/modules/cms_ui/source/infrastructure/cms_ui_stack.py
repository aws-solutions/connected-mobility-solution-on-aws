# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
from os.path import abspath, dirname
from typing import Any

# AWS Libraries
from aws_cdk import Aws, CfnMapping, Stack, Tags
from constructs import Construct

# CMS Common Library
from cms_common.config.ssm import get_resolvable_ssm_deployment_uuid
from cms_common.config.stack_inputs import S3AssetConfigInputs, SolutionConfigInputs
from cms_common.constructs.app_registry import AppRegistryConstruct, AppRegistryInputs
from cms_common.constructs.app_unique_id import AppUniqueId
from cms_common.constructs.cdk_lambda_vpc_config_construct import (
    CDKLambdasVpcConfigConstruct,
)
from cms_common.constructs.custom_resource_lambda import CustomResourceLambdaConstruct
from cms_common.constructs.lambda_dependencies import LambdaDependenciesConstruct
from cms_common.constructs.vpc_construct import VpcConstruct

# Connected Mobility Solution on AWS
from .constructs.authorization_lambda import AuthorizationLambdaConstruct
from .constructs.cognito_app_client import CognitoAppClientConstruct
from .constructs.fleet_management_api import FleetManagementAPIConstruct
from .constructs.location_map import LocationMapConstruct
from .constructs.module_integration import ModuleInputsConstruct, ModuleOutputsConstruct
from .constructs.user_interface_config import UserInterfaceConfigConstruct
from .constructs.user_interface_deployment import UserInterfaceDeploymentConstruct


class CmsUIStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        s3_asset_config_inputs: S3AssetConfigInputs,
        solution_config_inputs: SolutionConfigInputs,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        CfnMapping(
            self,
            "Solution",
            mapping={
                "AssetsConfig": {
                    "S3AssetBucketBaseName": s3_asset_config_inputs.bucket_base_name,
                    "S3AssetKeyPrefix": s3_asset_config_inputs.object_key_prefix,
                },
            },
        )

        AppRegistryConstruct(
            self,
            "app-registry-construct",
            app_registry_inputs=AppRegistryInputs(
                application_name=Aws.STACK_NAME,
                application_type=solution_config_inputs.application_type,
                solution_id=solution_config_inputs.solution_id,
                solution_name=solution_config_inputs.solution_name,
                solution_version=solution_config_inputs.solution_version,
            ),
        )

        module_inputs_construct = ModuleInputsConstruct(
            self, "module-inputs", solution_config_inputs=solution_config_inputs
        )

        app_unique_id = module_inputs_construct.module_config_inputs.app_unique_id

        # Check if a config stack for the app unique id is registered. Fail stack
        # creation if it is not registered. If config stack exists, then create an SSM
        # parameter to register the module with the app unique id.
        register_module_with_app_unique_id = AppUniqueId.register_module(
            self,
            app_unique_id=app_unique_id,
            module_name=solution_config_inputs.module_short_name,
        )

        deployment_uuid = get_resolvable_ssm_deployment_uuid(
            app_unique_id=app_unique_id
        )

        self.cms_ui_construct = CmsUiConstruct(
            self,
            "cms-ui",
            solution_config_inputs=solution_config_inputs,
            module_inputs_construct=module_inputs_construct,
        )
        self.cms_ui_construct.node.add_dependency(register_module_with_app_unique_id)

        Tags.of(self.cms_ui_construct).add("Solutions:DeploymentUUID", deployment_uuid)


class CmsUiConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        solution_config_inputs: SolutionConfigInputs,
        module_inputs_construct: ModuleInputsConstruct,
    ) -> None:
        super().__init__(scope, construct_id)

        vpc_construct = VpcConstruct(
            self, "vpc-construct", vpc_config=module_inputs_construct.vpc_config
        )

        self.cdk_lambdas_vpc_construct = CDKLambdasVpcConfigConstruct(
            self,
            "cdk-lambdas-vpc-construct",
            vpc_construct=vpc_construct,
            subnets=module_inputs_construct.vpc_config.private_subnets,
        )

        dependency_layer_construct = LambdaDependenciesConstruct(
            self,
            "dependency-layer-construct",
            pipfile_lock_dir=dirname(dirname(dirname(abspath(__file__)))),
            dependency_layer_path=f"{os.getcwd()}/deployment/dist/lambda/cms_ui_dependency_layer",
        )

        custom_resource_construct = CustomResourceLambdaConstruct(
            self,
            "custom-resource-construct",
            dependency_layer=dependency_layer_construct.dependency_layer,
            unique_id=module_inputs_construct.app_unique_id,
            name=solution_config_inputs.module_short_name,
            asset_path=f"{os.getcwd()}/deployment/dist/lambda/custom_resource.zip",
            user_agent_string=solution_config_inputs.get_user_agent_string(),
            vpc_construct=vpc_construct,
        )

        user_interface_deployment = UserInterfaceDeploymentConstruct(
            self,
            "user-interface-distribution-construct",
            module_inputs=module_inputs_construct,
            vpc_construct=vpc_construct,
        )

        cognito_app_client_construct = CognitoAppClientConstruct(
            self,
            "cognito-app-client-construct",
            app_unique_id=module_inputs_construct.app_unique_id,
            module_inputs=module_inputs_construct,
            user_interface_deployment=user_interface_deployment,
        )

        authorization_lambda_construct = AuthorizationLambdaConstruct(  # nosec
            self,
            "authorization-lambda-construct",
            app_unique_id=module_inputs_construct.app_unique_id,
            solution_config_inputs=solution_config_inputs,
            dependency_layer=dependency_layer_construct.dependency_layer,
            token_validation_lambda_arn=module_inputs_construct.token_validation.lambda_arn,
            vpc_construct=vpc_construct,
            cognito_app_client=cognito_app_client_construct,
        )

        fleet_management_api_construct = FleetManagementAPIConstruct(
            self,
            "fleet-management-api-construct",
            app_unique_id=module_inputs_construct.app_unique_id,
            solution_config_inputs=solution_config_inputs,
            authorization_lambda_construct=authorization_lambda_construct,
            vpc_construct=vpc_construct,
            openapi_definition_path=f"{os.getcwd()}/source/smithy/build/smithy/source/openapi/FleetManagement.openapi.json",
        )

        location_map_construct = LocationMapConstruct(
            self,
            "location-map-construct",
            app_unique_id=module_inputs_construct.app_unique_id,
            cognito_config=module_inputs_construct.cognito_config,
            cognito_app_client=cognito_app_client_construct,
        )

        user_interface_config = UserInterfaceConfigConstruct(
            self,
            "user-interface-config-construct",
            module_inputs=module_inputs_construct,
            custom_resource_lambda_construct=custom_resource_construct,
            cognito_app_client=cognito_app_client_construct,
            location_map=location_map_construct,
            user_interface_deployment=user_interface_deployment,
            fleet_management_api=fleet_management_api_construct,
        )

        ModuleOutputsConstruct(
            self,
            "cms-ui-module-outputs",
            app_unique_id=module_inputs_construct.app_unique_id,
            solution_config_inputs=solution_config_inputs,
            fleet_management_api_url=fleet_management_api_construct.api.url,
            ui_cf_url=f"https://{user_interface_deployment.cloudfront_dist.cloud_front_web_distribution.domain_name}",
            ui_config_s3_path=user_interface_config.s3_config_path,
            ui_app_client_id=cognito_app_client_construct.cms_ui_client_id,
        )
