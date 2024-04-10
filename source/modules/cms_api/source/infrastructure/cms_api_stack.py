# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
from os.path import abspath, dirname, join
from typing import Any

# AWS Libraries
from aws_cdk import Aws, CfnMapping, Stack, Tags
from constructs import Construct

# CMS Common Library
from cms_common.config.resource_names import ResourceName, ResourcePrefix
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
from .constructs.appsync_api import AppSyncAPIConstruct
from .constructs.athena_data_source import AppSyncAthenaDataSourceConstruct
from .constructs.authorization_lambda import AuthorizationLambdaConstruct
from .constructs.module_integration import ModuleInputsConstruct, ModuleOutputsConstruct


class CmsAPIStack(Stack):
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

        self.api_construct = CmsAPIConstruct(
            self,
            "cms-api",
            module_inputs_construct=module_inputs_construct,
            solution_config_inputs=solution_config_inputs,
        )
        self.api_construct.node.add_dependency(register_module_with_app_unique_id)

        Tags.of(self.api_construct).add("Solutions:DeploymentUUID", deployment_uuid)


class CmsAPIConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        solution_config_inputs: SolutionConfigInputs,
        module_inputs_construct: ModuleInputsConstruct,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id)
        AppRegistryConstruct(
            self,
            "app-registry",
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

        dependency_layer_construct = LambdaDependenciesConstruct(
            self,
            "dependency-layer",
            pipfile_path=f"{dirname(dirname(dirname(abspath(__file__))))}/Pipfile",
            dependency_layer_path=f"{os.getcwd()}/source/infrastructure/cms_api_dependency_layer",
        )

        # Authorization Lambda
        authorization_lambda_construct = AuthorizationLambdaConstruct(  # nosec
            self,
            "authorization-lambda",
            app_unique_id=module_inputs_construct.app_unique_id,
            solution_config_inputs=solution_config_inputs,
            dependency_layer=dependency_layer_construct.dependency_layer,
            token_validation_lambda_arn=module_inputs_construct.token_validation.lambda_arn,
            vpc_construct=vpc_construct,
        )

        # Combines type and operations graphql files
        schema_dir_path = join(dirname(abspath(__file__)), "assets/graphql/schemas")
        schema_file_name = "vss_schema.graphql"
        generate_graphql_schema(
            schemas_path=schema_dir_path, bundled_schema_file_name=schema_file_name
        )

        # AppSync API
        appsync_api = AppSyncAPIConstruct(
            self,
            "appsync-api",
            name=ResourceName.hyphen_separated(
                prefix=ResourcePrefix.hyphen_separated(
                    app_unique_id=module_inputs_construct.app_unique_id,
                    module_name=solution_config_inputs.module_short_name,
                ),
                name="appsync-api",
            ),
            schema_path=join(schema_dir_path, schema_file_name),
            authorization_lambda=authorization_lambda_construct.authorization_lambda,
        )

        # Athena Data Source
        appsync_athena_data_source = AppSyncAthenaDataSourceConstruct(
            self,
            "appsync-athena-data-source",
            app_unique_id=module_inputs_construct.app_unique_id,
            solution_config_inputs=solution_config_inputs,
            appsync_api=appsync_api.graphql_api,
            bucket_arn=module_inputs_construct.root_bucket.bucket_arn,
            bucket_key_arn=module_inputs_construct.root_bucket.bucket_key_arn,
            glue_registry_name=module_inputs_construct.glue.registry_name,
            glue_schema_arn=module_inputs_construct.glue.schema_arn,
            glue_database_name=module_inputs_construct.glue.database_name,
            glue_table_name=module_inputs_construct.glue.table_name,
            dependency_layer=dependency_layer_construct.dependency_layer,
            metrics_url=module_inputs_construct.operational_metrics.metrics_url,
            report_metrics_enabled=module_inputs_construct.operational_metrics.report_metrics_enabled,
            deployment_uuid=module_inputs_construct.operational_metrics.deployment_uuid,
            vpc_construct=vpc_construct,
        )

        ModuleOutputsConstruct(
            self,
            "cms-api-module-outputs",
            app_unique_id=module_inputs_construct.app_unique_id,
            solution_config_inputs=solution_config_inputs,
            athena_result_bucket_name=appsync_athena_data_source.athena_result_bucket.bucket.bucket_name,
            athena_result_bucket_arn=appsync_athena_data_source.athena_result_bucket.bucket.bucket_arn,
            athena_result_bucket_key_arn=appsync_athena_data_source.athena_result_bucket.key.key_arn,
            athena_workgroup_name=appsync_athena_data_source.athena_workgroup.name,
            appsync_graphql_url=appsync_api.graphql_api.graphql_url,
        )


def generate_graphql_schema(schemas_path: str, bundled_schema_file_name: str) -> None:
    bundled_schema = ""
    for file_name in os.listdir(schemas_path):
        if file_name != bundled_schema_file_name:
            with open(
                join(schemas_path, file_name),
                "r",
                encoding="utf-8",
            ) as file:
                bundled_schema += file.read()

    with open(
        join(schemas_path, bundled_schema_file_name),
        "w",
        encoding="utf-8",
    ) as graphql_schema_file:
        graphql_schema_file.write(bundled_schema)
