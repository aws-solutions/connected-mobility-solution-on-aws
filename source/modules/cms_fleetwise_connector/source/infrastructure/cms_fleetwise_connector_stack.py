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
from cms_common.config.resource_names import ResourceName
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
from .constructs.fleetwise_config import FleetWiseConfigConstruct
from .constructs.module_integration import ModuleInputsConstruct, ModuleOutputsConstruct
from .constructs.s3_glue_athena import S3GlueAthenaConstruct
from .constructs.timestream import TimestreamConstruct
from .constructs.timestream_to_s3.fleetwise_timestream_to_s3_step_function import (
    FleetWiseTimestreamToS3Construct,
)


class CmsFleetWiseConnectorStack(Stack):
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

        module_inputs = ModuleInputsConstruct(
            self, "module-inputs", solution_config_inputs=solution_config_inputs
        )

        app_unique_id = module_inputs.module_config_inputs.app_unique_id

        # Check if a config stack for the app unique id is registered. Fail stack
        # creation if it is not registered. If config stack exists, then create an SSM
        # parameter to register the module with the app unique id.
        register_module_with_app_unique_id = AppUniqueId.register_module(
            self,
            app_unique_id=app_unique_id,
            module_name=solution_config_inputs.module_short_name,
        )

        vpc_construct = VpcConstruct(
            self, "vpc-construct", vpc_config=module_inputs.vpc_config
        )

        self.cdk_lambdas_vpc_construct = CDKLambdasVpcConfigConstruct(
            self,
            "cdk-lambdas-vpc-construct",
            vpc_construct=vpc_construct,
            subnets=module_inputs.vpc_config.private_subnets,
        )

        deployment_uuid = get_resolvable_ssm_deployment_uuid(
            app_unique_id=app_unique_id
        )

        fleetwise_connector_construct = CmsFleetWiseConnectorConstruct(
            self,
            "cms-fleetwise-connector",
            solution_config_inputs=solution_config_inputs,
            module_inputs=module_inputs,
            vpc_construct=vpc_construct,
        )
        fleetwise_connector_construct.node.add_dependency(
            register_module_with_app_unique_id
        )

        Tags.of(fleetwise_connector_construct).add(
            "Solutions:DeploymentUUID", deployment_uuid
        )


class CmsFleetWiseConnectorConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        solution_config_inputs: SolutionConfigInputs,
        module_inputs: ModuleInputsConstruct,
        vpc_construct: VpcConstruct,
    ) -> None:
        super().__init__(scope, construct_id)

        # The App Unique ID should be used as a prefix to all resources created by this deployment
        app_unique_id = module_inputs.module_config_inputs.app_unique_id

        # Timestream DB/Table
        timestream = TimestreamConstruct(
            self,
            "timestream",
            db_name=ResourceName.hyphen_separated(
                prefix=app_unique_id,
                name="fleetwise-connector",
            ),
            table_name="fleetwise-cms-store",
        )

        fleetwise_config = FleetWiseConfigConstruct(
            self,
            "fleetwise-config",
            app_unique_id=app_unique_id,
            solution_config_inputs=solution_config_inputs,
            timestream_table_arn=timestream.timestream_table.attr_arn,
            timestream_kms_key_arn=timestream.timestream_kms_key.key_arn,
        )

        dependency_layer_construct = LambdaDependenciesConstruct(
            self,
            "dependency-layer",
            pipfile_lock_dir=dirname(dirname(dirname(abspath(__file__)))),
            dependency_layer_path=f"{os.getcwd()}/deployment/dist/lambda/cms_fleetwise_connector_dependency_layer",
        )

        FleetWiseTimestreamToS3Construct(
            self,
            "fleetwise-timestream-to-s3",
            solution_config_inputs=solution_config_inputs,
            module_config=module_inputs.module_config_inputs,
            telemetry_bucket=module_inputs.telemetry_bucket,
            operational_metrics=module_inputs.operational_metrics,
            timestream=timestream.outputs,
            dependency_layer=dependency_layer_construct.dependency_layer,
            vpc_construct=vpc_construct,
        )

        S3GlueAthenaConstruct(
            self,
            "s3-glue-athena",
            module_config=module_inputs.module_config_inputs,
            solution_config_inputs=solution_config_inputs,
            telemetry_bucket=module_inputs.telemetry_bucket,
            vpc_construct=vpc_construct,
        )

        ModuleOutputsConstruct(
            self,
            "cms-fleetwise-connector-module-outputs",
            module_config=module_inputs.module_config_inputs,
            timestream=timestream.outputs,
            fleetwise_execution_role_arn=fleetwise_config.fleetwise_execution_role.role_arn,
        )
