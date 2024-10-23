# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
from os.path import abspath, dirname
from typing import Any

# AWS Libraries
from aws_cdk import Aws, CfnMapping, CfnResource, Stack, Tags
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
from .constructs.cloudfront import CloudFrontConstruct
from .constructs.cognito import CognitoConstruct
from .constructs.console import ConsoleConstruct
from .constructs.module_integration import ModuleInputsConstruct, ModuleOutputsConstruct
from .constructs.simulator import SimulatorConstruct
from .constructs.storage import StorageConstruct
from .constructs.vsapi import VSApiConstruct


class CmsVehicleSimulatorStack(Stack):
    def __init__(
        self,
        scope: Construct,
        stack_id: str,
        solution_config_inputs: SolutionConfigInputs,
        s3_asset_config_inputs: S3AssetConfigInputs,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, stack_id, **kwargs)

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

        module_inputs_construct = ModuleInputsConstruct(self, "module-inputs-construct")

        # Check if a config stack for the app unique id is registered. Fail stack
        # creation if it is not registered. If config stack exists, then create an SSM
        # parameter to register the module with the app unique id.
        register_module_with_app_unique_id = AppUniqueId.register_module(
            self,
            app_unique_id=module_inputs_construct.app_unique_id,
            module_name=solution_config_inputs.module_name,
        )

        deployment_uuid = get_resolvable_ssm_deployment_uuid(
            app_unique_id=module_inputs_construct.app_unique_id
        )

        self.vehicle_simulator_construct = CmsVehicleSimulatorConstruct(
            self,
            "cms-vehicle-simulator",
            solution_config_inputs=solution_config_inputs,
            module_inputs_construct=module_inputs_construct,
        )
        self.vehicle_simulator_construct.node.add_dependency(
            register_module_with_app_unique_id
        )

        Tags.of(self.vehicle_simulator_construct).add(
            "Solutions:DeploymentUUID", deployment_uuid
        )


class CmsVehicleSimulatorConstruct(Construct):
    IOT_TOPIC_PREFIX: str = "cms/data/simulated"
    API_GATEWAY_STAGE: str = "dev"

    def __init__(
        self,
        scope: Stack,
        stack_id: str,
        solution_config_inputs: SolutionConfigInputs,
        module_inputs_construct: ModuleInputsConstruct,
    ) -> None:
        super().__init__(scope, stack_id)

        vpc_construct = VpcConstruct(
            self, "vpc-construct", vpc_config=module_inputs_construct.vpc_config
        )

        self.cdk_lambdas_vpc_construct = CDKLambdasVpcConfigConstruct(
            self,
            "cdk-lambdas-vpc-construct",
            vpc_construct=vpc_construct,
            subnets=module_inputs_construct.vpc_config.private_subnets,
        )

        storage_construct = StorageConstruct(self, "storage-construct")

        dependency_layer_construct = LambdaDependenciesConstruct(
            self,
            "dependency-layer-construct",
            pipfile_path=f"{dirname(dirname(dirname(abspath(__file__))))}/Pipfile",
            dependency_layer_path=f"{os.getcwd()}/source/infrastructure/cms_vehicle_simulator_dependency_layer",
        )

        custom_resource_construct = CustomResourceLambdaConstruct(
            self,
            "custom-resource-construct",
            dependency_layer=dependency_layer_construct.dependency_layer,
            unique_id=module_inputs_construct.app_unique_id,
            name=solution_config_inputs.module_short_name,
            asset_path="dist/lambda/custom_resource.zip",
            user_agent_string=solution_config_inputs.get_user_agent_string(),
            vpc_construct=vpc_construct,
        )

        cloudfront_construct = CloudFrontConstruct(
            self,
            "cloudfront-construct",
            app_unique_id=module_inputs_construct.app_unique_id,
            solution_config_inputs=solution_config_inputs,
        )

        cognito_construct = CognitoConstruct(
            self,
            "cognito-construct",
            admin_email=module_inputs_construct.admin_email.value_as_string,
            cloudfront_domain_name=cloudfront_construct.console_cloudfront_dist.cloud_front_web_distribution.domain_name,
            custom_resource_lambda_construct=custom_resource_construct,
        )

        simulator_construct = SimulatorConstruct(
            self,
            "simulator-construct",
            app_unique_id=module_inputs_construct.app_unique_id,
            solution_config_inputs=solution_config_inputs,
            storage_construct=storage_construct,
            custom_resource_lambda_construct=custom_resource_construct,
            routes_bucket_arn=cloudfront_construct.routes_bucket.bucket_arn,
            dependency_layer=dependency_layer_construct.dependency_layer,
            iot_topic_prefix=self.IOT_TOPIC_PREFIX,
            vpc_construct=vpc_construct,
        )

        vs_api_construct = VSApiConstruct(
            self,
            "vs-api-construct",
            solution_config_inputs=solution_config_inputs,
            storage_construct=storage_construct,
            simulator_construct=simulator_construct,
            cloudfront_domain_name=cloudfront_construct.console_cloudfront_dist.cloud_front_web_distribution.domain_name,
            user_pool_arn=cognito_construct.user_pool.user_pool_arn,
            api_gateway_stage=self.API_GATEWAY_STAGE,
            vpc_construct=vpc_construct,
        )

        ConsoleConstruct(
            self,
            "console-construct",
            template_folder_path="source/infrastructure/assets/templates",
            api_id=vs_api_construct.chalice.sam_template.get_resource("RestAPI").ref,
            api_endpoint=vs_api_construct.rest_api_endpoint,
            storage_construct=storage_construct,
            cloudfront_construct=cloudfront_construct,
            custom_resource_lambda_construct=custom_resource_construct,
            cognito_construct=cognito_construct,
            iot_endpoint=simulator_construct.iot_endpoint,
            iot_topic_prefix=self.IOT_TOPIC_PREFIX,
            vpc_construct=vpc_construct,
        )

        ModuleOutputsConstruct(
            self,
            "module-outputs-construct",
            cognito_construct=cognito_construct,
            cloudfront_construct=cloudfront_construct,
            vs_api_construct=vs_api_construct,
            api_gateway_stage=self.API_GATEWAY_STAGE,
            admin_email=module_inputs_construct.admin_email.value_as_string,
        )

        scope.template_options.template_format_version = "2010-09-09"
        scope.template_options.metadata = {
            "AWS::CloudFormation::Interface": {
                "ParameterGroups": [
                    {
                        "Label": {"default": "Console access"},
                        "Parameters": [module_inputs_construct.admin_email.logical_id],
                    }
                ],
                "ParameterLabels": {
                    module_inputs_construct.admin_email.logical_id: {
                        "default": "* Console Administrator Email"
                    }
                },
            }
        }

        api_handler = (
            vs_api_construct.node.find_child("vs-api-chalice")
            .node.find_child("ChaliceApp")
            .node.find_child("APIHandler")
        )
        CfnResource.add_metadata(
            api_handler,  # type: ignore[arg-type]
            "cfn_nag",
            {
                "rules_to_suppress": [
                    {"id": "W89", "reason": "Ignore VPC requirements for now"},
                    {
                        "id": "W92",
                        "reason": "Ignore reserved concurrent executions for now",
                    },
                ]
            },
        )
