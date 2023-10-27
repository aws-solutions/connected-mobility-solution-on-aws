# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from os import listdir
from os.path import abspath, dirname, join
from typing import Any

# Third Party Libraries
from aws_cdk import Stack, Tags, aws_ssm
from constructs import Construct

# Connected Mobility Solution on AWS
from ..config.constants import APIConstants
from ..infrastructure.constructs.app_registry import AppRegistryConstruct
from .constructs.appsync_api import AppSyncAPIConstruct
from .constructs.athena_data_source import AppSyncAthenaDataSourceConstruct
from .constructs.authorization_lambda import AuthorizationLambdaConstruct
from .constructs.lambda_dependencies import LambdaDependenciesConstruct
from .constructs.module_integration import ModuleInputsConstruct, ModuleOutputsConstruct


class CmsAPIOnAwsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)
        deployment_uuid = aws_ssm.StringParameter.from_string_parameter_name(
            self,
            "deployment-uuid",
            f"/{APIConstants.STAGE}/cms/common/config/deployment-uuid",
        ).string_value

        api_construct = CmsAPIConstruct(self, "cms-api")

        Tags.of(api_construct).add("Solutions:DeploymentUUID", deployment_uuid)


class CmsAPIConstruct(Construct):
    def __init__(self, scope: Construct, construct_id: str) -> None:
        super().__init__(scope, construct_id)
        AppRegistryConstruct(
            self,
            "app-registry",
            application_name=APIConstants.APP_NAME,
            application_type=APIConstants.APPLICATION_TYPE,
            solution_id=APIConstants.SOLUTION_ID,
            solution_name=APIConstants.SOLUTION_NAME,
            solution_version=APIConstants.SOLUTION_VERSION,
        )

        module_inputs_construct = ModuleInputsConstruct(
            self,
            "module-inputs",
        )

        dependency_layer_construct = LambdaDependenciesConstruct(
            self,
            "dependency-layer",
            dependency_layer_dir_name="api_dependency_layer",
        )

        # Authorization Lambda
        authorization_lambda_construct = AuthorizationLambdaConstruct(  # nosec
            self,
            "authorization-lambda",
            dependency_layer=dependency_layer_construct.dependency_layer,
            token_validation_lambda_arn=module_inputs_construct.token_validation.lambda_arn,
            token_use="access",
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
            name=f"{APIConstants.APP_NAME}-appsync-api",
            schema_path=join(schema_dir_path, schema_file_name),
            authorization_lambda=authorization_lambda_construct.authorization_lambda,
        )

        # Athena Data Source
        appsync_athena_data_source = AppSyncAthenaDataSourceConstruct(
            self,
            "appsync-athena-data-source",
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
        )

        ModuleOutputsConstruct(
            self,
            "cms-api-module-outputs",
            athena_result_bucket_name=appsync_athena_data_source.athena_result_bucket.bucket.bucket_name,
            athena_result_bucket_arn=appsync_athena_data_source.athena_result_bucket.bucket.bucket_arn,
            athena_result_bucket_key_arn=appsync_athena_data_source.athena_result_bucket.key.key_arn,
            athena_workgroup_name=appsync_athena_data_source.athena_workgroup.name,
            appsync_graphql_url=appsync_api.graphql_api.graphql_url,
        )


def generate_graphql_schema(schemas_path: str, bundled_schema_file_name: str) -> None:
    bundled_schema = ""
    for file_name in listdir(schemas_path):
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
