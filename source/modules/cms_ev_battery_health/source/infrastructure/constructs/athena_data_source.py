# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0


# AWS Libraries
from aws_cdk import ArnFormat, CustomResource, Stack, aws_iam
from constructs import Construct

# CMS Common Library
from cms_common.constructs.custom_resource_lambda import CustomResourceLambdaConstruct
from cms_common.policy_generators.kms import generate_kms_policy_statement_from_key_arn

# Connected Mobility Solution on AWS
from ...handlers.custom_resource.function.lib.custom_resource_type_enum import (
    CustomResourceType,
)
from ...handlers.custom_resource.function.lib.data_sources import GrafanaDataSourceType
from .grafana_api_key import GrafanaApiKeyConstruct
from .grafana_workspace import GrafanaWorkspaceConstruct
from .module_integration import AthenaDataSourceProperties


class AthenaDataSourceConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        athena_data_source_properties: AthenaDataSourceProperties,
        grafana_api_key_construct: GrafanaApiKeyConstruct,
        grafana_workspace_construct: GrafanaWorkspaceConstruct,
        custom_resource_lambda_construct: CustomResourceLambdaConstruct,
    ) -> None:
        super().__init__(scope, construct_id)

        grafana_workspace_construct.add_policy_to_grafana_workspace(
            policy=aws_iam.Policy(
                self,
                "grafana-workspace-policy",
                statements=[
                    aws_iam.PolicyStatement(
                        actions=[
                            "athena:GetDatabase",
                            "athena:GetDataCatalog",
                            "athena:GetTableMetadata",
                            "athena:ListDatabases",
                            "athena:ListDataCatalogs",
                            "athena:ListTableMetadata",
                            "athena:ListWorkGroups",
                        ],
                        effect=aws_iam.Effect.ALLOW,
                        resources=[
                            Stack.of(self).format_arn(
                                service="athena",
                                resource="workgroup",
                                resource_name=athena_data_source_properties.athena_workgroup_name,
                                arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                            ),
                            Stack.of(self).format_arn(
                                service="athena",
                                resource="datacatalog",
                                resource_name=athena_data_source_properties.glue_catalog_name,
                                arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                            ),
                        ],
                    ),
                    aws_iam.PolicyStatement(
                        actions=[
                            "athena:GetQueryExecution",
                            "athena:GetQueryResults",
                            "athena:GetWorkGroup",
                            "athena:StartQueryExecution",
                            "athena:StopQueryExecution",
                        ],
                        effect=aws_iam.Effect.ALLOW,
                        resources=[
                            Stack.of(self).format_arn(
                                service="athena",
                                resource="workgroup",
                                resource_name=athena_data_source_properties.athena_workgroup_name,
                                arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                            ),
                        ],
                        conditions={
                            "Null": {"aws:ResourceTag/GrafanaDataSource": "false"}
                        },
                    ),
                    aws_iam.PolicyStatement(
                        actions=[
                            "glue:GetSchemaVersion",
                        ],
                        effect=aws_iam.Effect.ALLOW,
                        resources=[
                            athena_data_source_properties.glue_schema_arn,
                            Stack.of(self).format_arn(
                                service="glue",
                                resource="registry",
                                arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                resource_name=athena_data_source_properties.glue_registry_name,
                            ),
                        ],
                    ),
                    aws_iam.PolicyStatement(
                        actions=[
                            "glue:GetDatabase",
                            "glue:GetDatabases",
                        ],
                        effect=aws_iam.Effect.ALLOW,
                        resources=[
                            Stack.of(self).format_arn(
                                service="glue",
                                resource="catalog",
                                arn_format=ArnFormat.NO_RESOURCE_NAME,
                            ),
                            Stack.of(self).format_arn(
                                service="glue",
                                resource="database",
                                arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                resource_name=athena_data_source_properties.glue_database_name,
                            ),
                        ],
                    ),
                    aws_iam.PolicyStatement(
                        actions=[
                            "glue:GetTable",
                            "glue:GetTables",
                        ],
                        effect=aws_iam.Effect.ALLOW,
                        resources=[
                            Stack.of(self).format_arn(
                                service="glue",
                                resource="catalog",
                                arn_format=ArnFormat.NO_RESOURCE_NAME,
                            ),
                            Stack.of(self).format_arn(
                                service="glue",
                                resource="database",
                                arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                resource_name=athena_data_source_properties.glue_database_name,
                            ),
                            Stack.of(self).format_arn(
                                service="glue",
                                resource="table",
                                arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                resource_name=f"{athena_data_source_properties.glue_database_name}/{athena_data_source_properties.glue_table_name}",
                            ),
                        ],
                    ),
                    aws_iam.PolicyStatement(
                        actions=[
                            "s3:GetBucketLocation",
                            "s3:GetObject",
                            "s3:ListBucket",
                            "s3:ListBucketMultipartUploads",
                            "s3:ListMultipartUploadParts",
                            "s3:AbortMultipartUpload",
                            "s3:CreateBucket",
                            "s3:PutObject",
                        ],
                        effect=aws_iam.Effect.ALLOW,
                        resources=[
                            f"{athena_data_source_properties.athena_results_bucket_arn}*",
                            f"{athena_data_source_properties.athena_data_storage_bucket_arn}*",
                        ],
                    ),
                    generate_kms_policy_statement_from_key_arn(
                        kms_encryption_key_arn=athena_data_source_properties.athena_data_storage_bucket_key_arn,
                        allow_encrypt=False,
                    ),
                    generate_kms_policy_statement_from_key_arn(
                        kms_encryption_key_arn=athena_data_source_properties.athena_results_bucket_key_arn,
                        allow_encrypt=True,
                    ),
                ],
            )
        )

        athena_data_source_custom_resource_policy = aws_iam.Policy(
            self,
            "custom-resource-policy",
            statements=[
                aws_iam.PolicyStatement(
                    actions=[
                        "secretsmanager:GetSecretValue",
                    ],
                    effect=aws_iam.Effect.ALLOW,
                    resources=[
                        grafana_api_key_construct.secret.secret_arn,
                    ],
                ),
            ],
        )
        custom_resource_lambda_construct.add_policy_to_custom_resource_lambda(
            policy=athena_data_source_custom_resource_policy
        )

        self.data_source = CustomResource(
            self,
            "create-grafana-athena-datasource-custom-resource",
            service_token=custom_resource_lambda_construct.function.function_arn,
            resource_type=f"Custom::{CustomResourceType.ResourceType.CREATE_GRAFANA_DATA_SOURCE.value}",
            properties={
                "Resource": CustomResourceType.ResourceType.CREATE_GRAFANA_DATA_SOURCE.value,
                "GrafanaWorkspaceEndpoint": grafana_workspace_construct.workspace.attr_endpoint,
                "GrafanaApiKeySecretArn": grafana_api_key_construct.secret.secret_arn,
                "DataSourceType": GrafanaDataSourceType.ATHENA.value,
                "DataSourceProperties": {
                    "catalog": athena_data_source_properties.glue_catalog_name,
                    "database": athena_data_source_properties.glue_database_name,
                    "workgroup": athena_data_source_properties.athena_workgroup_name,
                    "defaultRegion": Stack.of(self).region,
                },
            },
        )
        self.data_source.node.add_dependency(grafana_api_key_construct)
