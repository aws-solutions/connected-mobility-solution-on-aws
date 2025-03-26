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
from cms_common.constructs.lambda_dependencies import LambdaDependenciesConstruct
from cms_common.constructs.vpc_construct import VpcConstruct

# Connected Mobility Solution on AWS
from .constructs.authorization_code_exchange_lambda import (
    AuthorizationCodeExchangeLambdaConstruct,
)
from .constructs.module_integration import ModuleInputsConstruct, ModuleOutputsConstruct
from .constructs.token_validation_lambda import TokenValidationLambdaConstruct


class CmsAuthStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        solution_config_inputs: SolutionConfigInputs,
        s3_asset_config_inputs: S3AssetConfigInputs,
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

        module_inputs_construct = ModuleInputsConstruct(self, "module-inputs-construct")
        app_unique_id = module_inputs_construct.app_unique_id

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

        self.auth_construct = CmsAuthConstruct(
            self,
            "cms-auth",
            solution_config_inputs=solution_config_inputs,
            module_inputs_construct=module_inputs_construct,
        )
        self.auth_construct.node.add_dependency(register_module_with_app_unique_id)

        Tags.of(self.auth_construct).add("Solutions:DeploymentUUID", deployment_uuid)


class CmsAuthConstruct(Construct):
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

        lambda_dependencies_construct = LambdaDependenciesConstruct(
            self,
            "dependency-layer",
            pipfile_lock_dir=dirname(dirname(dirname(abspath(__file__)))),
            dependency_layer_path=f"{os.getcwd()}/deployment/dist/lambda/cms_auth_dependency_layer",
        )

        token_validation_lambda_construct = TokenValidationLambdaConstruct(
            self,
            "token-validation-lambda",
            app_unique_id=module_inputs_construct.app_unique_id,
            solution_config_inputs=solution_config_inputs,
            dependency_layer=lambda_dependencies_construct.dependency_layer,
            identity_provider_id=module_inputs_construct.identity_provider_id,
            vpc_construct=vpc_construct,
        )

        authorization_code_exchange_lambda_construct = (
            AuthorizationCodeExchangeLambdaConstruct(
                self,
                "authorization-code-exchange-lambda",
                app_unique_id=module_inputs_construct.app_unique_id,
                solution_config_inputs=solution_config_inputs,
                dependency_layer=lambda_dependencies_construct.dependency_layer,
                identity_provider_id=module_inputs_construct.identity_provider_id,
                vpc_construct=vpc_construct,
            )
        )

        ModuleOutputsConstruct(
            self,
            "module-outputs",
            app_unique_id=module_inputs_construct.app_unique_id,
            authorization_code_exchange_lambda_arn=authorization_code_exchange_lambda_construct.lambda_function.function_arn,
            token_validation_lambda_arn=token_validation_lambda_construct.lambda_function.function_arn,
        )
