# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from os.path import abspath, dirname, join

# Third Party Libraries
from aws_cdk import (
    ArnFormat,
    CfnTag,
    Duration,
    Stack,
    aws_appsync,
    aws_athena,
    aws_iam,
    aws_lambda,
)
from constructs import Construct

# Connected Mobility Solution on AWS
from ...config.constants import APIConstants
from ..lib.policy_generators import generate_lambda_cloudwatch_logs_policy_document
from .cmk_encrypted_s3 import CMKEncryptedS3Construct


class AppSyncAthenaDataSourceConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        appsync_api: aws_appsync.GraphqlApi,
        bucket_arn: str,
        bucket_key_arn: str,
        glue_registry_name: str,
        glue_database_name: str,
        glue_schema_arn: str,
        glue_table_name: str,
        dependency_layer: aws_lambda.LayerVersion,
        metrics_url: str,
        report_metrics_enabled: str,
        deployment_uuid: str,
    ) -> None:
        super().__init__(scope, construct_id)

        self.athena_result_bucket = CMKEncryptedS3Construct(
            self, "athena-result-cmk-s3"
        )

        self.athena_workgroup = aws_athena.CfnWorkGroup(
            self,
            "workgroup",
            name="cms-athena-workgroup",
            description="Athena Workgroup for CMS",
            recursive_delete_option=True,
            work_group_configuration=aws_athena.CfnWorkGroup.WorkGroupConfigurationProperty(
                result_configuration=aws_athena.CfnWorkGroup.ResultConfigurationProperty(
                    output_location=f"s3://{self.athena_result_bucket.bucket.bucket_name}",
                    encryption_configuration=aws_athena.CfnWorkGroup.EncryptionConfigurationProperty(
                        encryption_option="SSE_KMS",
                        kms_key=self.athena_result_bucket.key.key_arn,
                    ),
                ),
                enforce_work_group_configuration=True,
            ),
            tags=[CfnTag(key="GrafanaDataSource", value="true")],
        )

        athena_data_source_lambda_name = (
            f"{APIConstants.APP_NAME}-athena-data-source-lambda"
        )

        athena_data_source_lambda_role = aws_iam.Role(
            self,
            "lambda-role",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            path="/",
            inline_policies={
                "cloudwatch-logs-policy": generate_lambda_cloudwatch_logs_policy_document(
                    self, lambda_function_name=athena_data_source_lambda_name
                ),
                "s3-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "s3:ListBucket",
                                "s3:GetObject",
                                "s3:GetBucketLocation",
                                "s3:ListBucketMultipartUploads",
                                "s3:AbortMultipartUpload",
                                "s3:PutObject",
                                "s3:ListMultipartUploadParts",
                            ],
                            resources=[
                                bucket_arn,
                                f"{bucket_arn}/*",
                                self.athena_result_bucket.bucket.bucket_arn,
                                f"{self.athena_result_bucket.bucket.bucket_arn}/*",
                            ],
                        ),
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "kms:Decrypt",
                                "kms:GenerateDataKey",
                            ],
                            resources=[
                                bucket_key_arn,
                                self.athena_result_bucket.key.key_arn,
                            ],
                        ),
                    ]
                ),
                "glue-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "glue:GetSchemaVersion",
                            ],
                            resources=[
                                glue_schema_arn,
                                Stack.of(self).format_arn(
                                    service="glue",
                                    resource="registry",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                    resource_name=glue_registry_name,
                                ),
                            ],
                        ),
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=["glue:GetTable"],
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
                                    resource_name=glue_database_name,
                                ),
                                Stack.of(self).format_arn(
                                    service="glue",
                                    resource="table",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                    resource_name=f"{glue_database_name}/{glue_table_name}",
                                ),
                            ],
                        ),
                    ]
                ),
                "athena-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "athena:StartQueryExecution",
                                "athena:GetQueryExecution",
                                "athena:GetQueryResults",
                            ],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="athena",
                                    resource="workgroup",
                                    resource_name=self.athena_workgroup.name,
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                )
                            ],
                        )
                    ]
                ),
            },
        )

        athena_data_source_lambda = aws_lambda.Function(
            self,
            "lambda",
            function_name=athena_data_source_lambda_name,
            code=aws_lambda.Code.from_asset("source/handlers"),
            description="CMS API Athena data source Lambda",
            handler="athena_data_source.main.handler",
            runtime=aws_lambda.Runtime.PYTHON_3_10,
            layers=[dependency_layer],
            role=athena_data_source_lambda_role,
            timeout=Duration.minutes(1),
            environment={
                # meta environmental variables
                "USER_AGENT_STRING": APIConstants.USER_AGENT_STRING,
                "SOLUTION_ID": APIConstants.SOLUTION_ID,
                "SOLUTION_VERSION": APIConstants.SOLUTION_VERSION,
                "AWS_ACCOUNT_ID": Stack.of(self).account,
                "METRICS_SOLUTION_URL": metrics_url,
                "REPORT_METRICS_ENABLED": report_metrics_enabled,
                "DEPLOYMENT_UUID": deployment_uuid,
                # functional environmental variables
                "GLUE_DATABASE_NAME": glue_database_name,
                "GLUE_TABLE_NAME": glue_table_name,
                "ATHENA_WORKGROUP": self.athena_workgroup.name,
                "RECORD_LIMIT": "100",
            },
        )

        athena_data_source = appsync_api.add_lambda_data_source(
            "lambda-data-source",
            athena_data_source_lambda,
            description="Lambda backed data source for Athena",
        )

        athena_data_source.create_resolver(
            "resolver-get-vehicle",
            type_name="Query",
            field_name="getVehicle",
            request_mapping_template=aws_appsync.MappingTemplate.from_file(
                join(
                    dirname(dirname(abspath(__file__))),
                    "assets/graphql/mapping_templates/lambda_request.vtl",
                )
            ),
            response_mapping_template=aws_appsync.MappingTemplate.lambda_result(),
        )

        athena_data_source.create_resolver(
            "resolver-list-vehicles",
            type_name="Query",
            field_name="listVehicles",
            request_mapping_template=aws_appsync.MappingTemplate.from_file(
                join(
                    dirname(dirname(abspath(__file__))),
                    "assets/graphql/mapping_templates/lambda_request.vtl",
                )
            ),
            response_mapping_template=aws_appsync.MappingTemplate.lambda_result(),
        )
