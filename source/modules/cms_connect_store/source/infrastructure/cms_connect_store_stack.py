# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json
import os
from os.path import abspath, dirname
from typing import Any, Dict

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
from .constructs.alerts_construct import AlertsConstruct
from .constructs.cmk_encrypted_s3 import CMKEncryptedS3Construct
from .constructs.iot_core_to_s3_json import IoTCoreToS3JsonConstruct
from .constructs.iot_core_to_s3_parquet import IoTCoreToS3ParquetConstruct
from .constructs.module_integration import ModuleInputsConstruct, ModuleOutputsConstruct
from .constructs.s3_to_glue import S3ToGlueConstruct


class CmsConnectStoreStack(Stack):
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

        self.module_inputs_construct = ModuleInputsConstruct(
            self, "module-inputs-construct"
        )
        app_unique_id = self.module_inputs_construct.app_unique_id

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

        self.connect_store_construct = CmsConnectStoreConstruct(
            self,
            "connect-store",
            solution_config_inputs=solution_config_inputs,
            module_inputs_construct=self.module_inputs_construct,
        )
        self.connect_store_construct.node.add_dependency(
            register_module_with_app_unique_id
        )

        Tags.of(self.connect_store_construct).add(
            "Solutions:DeploymentUUID", deployment_uuid
        )


class CmsConnectStoreConstruct(Construct):
    DEFAULT_GLUE_CATALOG_NAME = "AwsDataCatalog"
    DEFAULT_GLUE_REGISTRY_NAME = "default-registry"  # This name is pre-specified by Glue, and allows the automatic creation of a registry
    IOT_CORE_DATA_QUERY = "SELECT * FROM 'cms/data/#'"
    IOT_CORE_NOTIFICATIONS_QUERY = "SELECT * from 'cms/notification/#'"

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        solution_config_inputs: SolutionConfigInputs,
        module_inputs_construct: ModuleInputsConstruct,
    ) -> None:
        super().__init__(scope, construct_id)

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

        vpc_construct = VpcConstruct(
            self, "vpc-construct", vpc_config=module_inputs_construct.vpc_config
        )

        self.cdk_lambdas_vpc_construct = CDKLambdasVpcConfigConstruct(
            self,
            "cdk-lambdas-vpc-construct",
            vpc_construct=vpc_construct,
            subnets=module_inputs_construct.vpc_config.private_subnets,
        )

        root_s3 = CMKEncryptedS3Construct(self, "root-s3-construct")

        dependency_layer_construct = LambdaDependenciesConstruct(
            self,
            "dependency-layer-construct",
            pipfile_path=f"{dirname(dirname(dirname(abspath(__file__))))}/Pipfile",
            dependency_layer_path=f"{os.getcwd()}/source/infrastructure/cms_connect_store_dependency_layer",
        )

        s3_to_glue = S3ToGlueConstruct(
            self,
            "glue-resources-construct",
            app_unique_id=module_inputs_construct.app_unique_id,
            schema_json=self.load_vss_schema(),
            default_registry_name=self.DEFAULT_GLUE_REGISTRY_NAME,
            root_s3_bucket=root_s3.bucket,
            solution_config_inputs=solution_config_inputs,
        )

        IoTCoreToS3JsonConstruct(
            self,
            "iot-core-to-s3-json-construct",
            app_unique_id=module_inputs_construct.app_unique_id,
            iot_core_query=self.IOT_CORE_DATA_QUERY,
            root_s3_bucket=root_s3.bucket,
            solution_config_inputs=solution_config_inputs,
        )

        iot_core_to_s3_parquet = IoTCoreToS3ParquetConstruct(
            self,
            "iot-core-to-s3-parquet-construct",
            app_unique_id=module_inputs_construct.app_unique_id,
            iot_core_query=self.IOT_CORE_DATA_QUERY,
            root_s3_bucket=root_s3.bucket,
            glue_resources=s3_to_glue.glue_resources,
            solution_config_inputs=solution_config_inputs,
        )
        iot_core_to_s3_parquet.node.add_dependency(s3_to_glue)

        AlertsConstruct(
            self,
            "alerts-construct",
            app_unique_id=module_inputs_construct.app_unique_id,
            solution_config_inputs=solution_config_inputs,
            dependency_layer=dependency_layer_construct.dependency_layer,
            alerts_publish_endpoint_url=module_inputs_construct.alerts_publish_endpoint_ssm_path,
            identity_provider_id=module_inputs_construct.identity_provider_id,
            vehicle_notifications_iot_core_query=self.IOT_CORE_NOTIFICATIONS_QUERY,
            vpc_construct=vpc_construct,
        )

        ModuleOutputsConstruct(
            self,
            "module-outputs-construct",
            app_unique_id=module_inputs_construct.app_unique_id,
            solution_config_inputs=solution_config_inputs,
            glue_resources=s3_to_glue.glue_resources,
            root_s3_bucket=root_s3.bucket,
            glue_catalog_name=self.DEFAULT_GLUE_CATALOG_NAME,
        )

    def load_vss_schema(self) -> Dict[str, Any]:
        with open(
            f"{os.path.dirname(os.path.realpath(__file__))}/assets/vss.json",
            encoding="utf-8",
        ) as file:
            vss_schema: Dict[str, Any] = json.load(file)
            return vss_schema
