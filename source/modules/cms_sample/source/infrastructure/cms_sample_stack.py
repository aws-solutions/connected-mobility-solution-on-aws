# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any

# AWS Libraries
from aws_cdk import Aws, CfnMapping, Stack, Tags
from constructs import Construct

# CMS Common Library
from cms_common.config.ssm import get_resolvable_ssm_deployment_uuid
from cms_common.config.stack_inputs import S3AssetConfigInputs, SolutionConfigInputs
from cms_common.constructs.app_registry import AppRegistryConstruct, AppRegistryInputs
from cms_common.constructs.app_unique_id import AppUniqueId

# Connected Mobility Solution on AWS
from .constructs.module_integration import ModuleInputsConstruct


class CmsSampleStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        solution_config_inputs: SolutionConfigInputs,
        s3_asset_config_inputs: S3AssetConfigInputs,
        **kwargs: Any
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

        cms_sample_construct = CmsSampleConstruct(
            self,
            "cms-sample",
        )
        cms_sample_construct.node.add_dependency(register_module_with_app_unique_id)

        Tags.of(cms_sample_construct).add("Solutions:DeploymentUUID", deployment_uuid)


class CmsSampleConstruct(Construct):
    def __init__(self, scope: Construct, construct_id: str, **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Implement module features and constructs here
