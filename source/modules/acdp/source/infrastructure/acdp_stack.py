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
from .constructs.backstage_assets import BackstageAssetsConstruct
from .constructs.cloudformation_role import CloudFormationRoleConstruct
from .constructs.cmk_encrypted_s3 import CMKEncryptedS3Construct
from .constructs.deployment_uuid_construct import DeploymentUUIDConstruct
from .constructs.module_deploy import ModuleDeployCodeBuildConstruct
from .constructs.module_integration import ModuleInputsConstruct, ModuleOutputsConstruct
from .constructs.pipelines import Pipelines


class AcdpStack(Stack):
    def __init__(
        self,
        scope: Construct,
        stack_id: str,
        solution_config_inputs: SolutionConfigInputs,
        s3_asset_config_inputs: S3AssetConfigInputs,
        backstage_s3_assets_key_prefix: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, stack_id, **kwargs)

        solution_mapping = CfnMapping(
            self,
            "Solution",
            mapping={
                "AssetsConfig": {
                    "S3AssetBucketBaseName": s3_asset_config_inputs.bucket_base_name,
                    "S3AssetKeyPrefix": s3_asset_config_inputs.object_key_prefix,
                },
                "Config": {
                    "SendAnonymousUsage": "Yes",
                },
            },
        )

        local_asset_bucket_construct = CMKEncryptedS3Construct(
            self, "backstage-asset-bucket-construct"
        )

        module_inputs_construct = ModuleInputsConstruct(
            self,
            "module-inputs-construct",
            solution_mapping=solution_mapping,
            backstage_s3_assets_key_prefix=backstage_s3_assets_key_prefix,
            local_asset_bucket_construct=local_asset_bucket_construct,
        )

        lambda_dependencies_construct = LambdaDependenciesConstruct(
            self,
            "acdp-dependency-layer",
            pipfile_path=f"{dirname(dirname(dirname(abspath(__file__))))}/Pipfile",
            dependency_layer_path=f"{os.getcwd()}/source/infrastructure/acdp_dependency_layer",
        )

        # SSM Parameter to register an app unique ID. This is done before initializing
        # any other resources so that the stack creation fails early if another stack
        # with the same app unique ID is already deployed.
        app_unique_id_ssm_parameter = AppUniqueId.register(
            self, app_unique_id=module_inputs_construct.acdp_uid
        )

        vpc_construct = VpcConstruct(
            self, "vpc-construct", vpc_config=module_inputs_construct.vpc_config
        )

        self.cdk_lambdas_vpc_construct = CDKLambdasVpcConfigConstruct(
            self,
            "cdk-lambdas-vpc-construct",
            vpc_construct=vpc_construct,
            subnets=module_inputs_construct.vpc_config.private_subnets,
        )

        custom_resource_construct = CustomResourceLambdaConstruct(
            self,
            "custom-resource-construct",
            dependency_layer=lambda_dependencies_construct.dependency_layer,
            unique_id=module_inputs_construct.acdp_uid,
            name=solution_config_inputs.module_short_name,
            asset_path="dist/lambda/custom_resource.zip",
            user_agent_string=solution_config_inputs.get_user_agent_string(),
            vpc_construct=vpc_construct,
        )

        deployment_uuid_construct = DeploymentUUIDConstruct(
            self,
            "deployment-uuid-construct",
            custom_resource_lambda_arn=custom_resource_construct.function.function_arn,
        )
        deployment_uuid = deployment_uuid_construct.uuid

        acdp_construct = AcdpConstruct(
            self,
            "acdp",
            solution_config_inputs=solution_config_inputs,
            deployment_uuid=deployment_uuid,
            module_inputs=module_inputs_construct,
            solution_mapping=solution_mapping,
            vpc_construct=vpc_construct,
            custom_resource_lambda_construct=custom_resource_construct,
        )
        acdp_construct.node.add_dependency(app_unique_id_ssm_parameter)

        # DeploymentUUID must be defined outside of any construct being tagged and have no dependencies on that construct
        Tags.of(acdp_construct).add("Solutions:DeploymentUUID", deployment_uuid)


class AcdpConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        solution_config_inputs: SolutionConfigInputs,
        deployment_uuid: str,
        module_inputs: ModuleInputsConstruct,
        solution_mapping: CfnMapping,
        vpc_construct: VpcConstruct,
        custom_resource_lambda_construct: CustomResourceLambdaConstruct,
    ) -> None:
        super().__init__(scope, construct_id)

        AppRegistryConstruct(
            self,
            "acdp-app-registry",
            app_registry_inputs=AppRegistryInputs(
                application_name=Aws.STACK_NAME,
                application_type=solution_config_inputs.application_type,
                solution_id=solution_config_inputs.solution_id,
                solution_name=solution_config_inputs.solution_name,
                solution_version=solution_config_inputs.solution_version,
            ),
        )

        cloudformation_role = CloudFormationRoleConstruct(self, "cloudformation-role")

        backstage_assets = BackstageAssetsConstruct(
            self,
            "backstage-assets-construct",
            solution_mapping=solution_mapping,
            solution_config_inputs=solution_config_inputs,
            local_asset_bucket_inputs=module_inputs.local_asset_bucket_inputs,
            custom_resource_lambda_construct=custom_resource_lambda_construct,
        )

        pipelines = Pipelines(
            self,
            "pipelines-construct",
            module_inputs=module_inputs,
            solution_mapping=solution_mapping,
            cloudformation_role_arn=cloudformation_role.role.role_arn,
            vpc_name=module_inputs.vpc_name,
            vpc=vpc_construct.vpc,
            private_subnet_selection=vpc_construct.private_subnet_selection,
            backstage_source_asset_zip_location=backstage_assets.backstage_source_asset_zip_location,
        )
        pipelines.node.add_dependency(backstage_assets)

        module_deploy_construct = ModuleDeployCodeBuildConstruct(
            self,
            "module-deploy-project",
            solution_mapping=solution_mapping,
            cloudformation_role_arn=cloudformation_role.role.role_arn,
            vpc=vpc_construct.vpc,
            private_subnet_selection=vpc_construct.private_subnet_selection,
            module_inputs=module_inputs,
        )

        ModuleOutputsConstruct(
            self,
            "module-outputs-construct",
            deployment_uuid=deployment_uuid,
            backstage_regional_asset_config_inputs=module_inputs.regional_asset_bucket_inputs,
            backstage_local_asset_bucket_config_inputs=module_inputs.local_asset_bucket_inputs,
            codebuild_project_arn=module_deploy_construct.codebuild_project.project_arn,
            acdp_config_ssm_prefix=module_inputs.acdp_config_ssm_prefix,
        )
