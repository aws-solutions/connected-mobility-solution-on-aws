# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from dataclasses import dataclass
from os.path import abspath, dirname, join

# AWS Libraries
from aws_cdk import (
    ArnFormat,
    CfnTag,
    Duration,
    Stack,
    aws_appsync,
    aws_athena,
    aws_ec2,
    aws_iam,
    aws_lambda,
)
from constructs import Construct

# CMS Common Library
from cms_common.config.resource_names import ResourceName, ResourcePrefix
from cms_common.config.stack_inputs import SolutionConfigInputs
from cms_common.constructs.encrypted_s3 import EncryptedS3Construct
from cms_common.constructs.vpc_construct import VpcConstruct
from cms_common.policy_generators.cloudwatch import (
    generate_lambda_cloudwatch_logs_policy_document,
)
from cms_common.policy_generators.ec2_vpc import generate_ec2_vpc_policy

# Connected Mobility Solution on AWS
from .module_integration import ModuleInputsConstruct


@dataclass(frozen=True)
class AppSyncAthenaDataSourceConstructInputs:
    appsync_api: aws_appsync.GraphqlApi
    bucket_arn: str
    glue_registry_name: str
    glue_database_name: str
    glue_schema_arn: str
    glue_table_name: str
    dependency_layer: aws_lambda.LayerVersion
    metrics_url: str
    report_metrics_enabled: str
    deployment_uuid: str
    vpc_construct: VpcConstruct


class AppSyncAthenaDataSourceConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        solution_config_inputs: SolutionConfigInputs,
        module_inputs: ModuleInputsConstruct,
        app_sync_athena_data_source_construct_inputs: AppSyncAthenaDataSourceConstructInputs,
    ) -> None:
        super().__init__(scope, construct_id)

        self.athena_result_bucket = EncryptedS3Construct(
            self,
            "athena-result-s3",
            log_lifecycle_rules=module_inputs.s3_log_lifecycle_rules,
        )

        self.athena_workgroup = aws_athena.CfnWorkGroup(
            self,
            "workgroup",
            name=ResourceName.hyphen_separated(
                prefix=ResourcePrefix.hyphen_separated(
                    app_unique_id=module_inputs.app_unique_id,
                    module_name=solution_config_inputs.module_short_name,
                ),
                name="athena-workgroup",
            ),
            description="Athena Workgroup for CMS",
            recursive_delete_option=True,
            work_group_configuration=aws_athena.CfnWorkGroup.WorkGroupConfigurationProperty(
                result_configuration=aws_athena.CfnWorkGroup.ResultConfigurationProperty(
                    output_location=f"s3://{self.athena_result_bucket.bucket.bucket_name}",
                    encryption_configuration=aws_athena.CfnWorkGroup.EncryptionConfigurationProperty(
                        encryption_option="SSE_S3",
                    ),
                ),
                enforce_work_group_configuration=True,
            ),
            tags=[CfnTag(key="GrafanaDataSource", value="true")],
        )

        athena_data_source_lambda_name = ResourceName.hyphen_separated(
            prefix=ResourcePrefix.hyphen_separated(
                app_unique_id=module_inputs.app_unique_id,
                module_name=solution_config_inputs.module_short_name,
            ),
            name="athena-data-source",
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
                                app_sync_athena_data_source_construct_inputs.bucket_arn,
                                f"{app_sync_athena_data_source_construct_inputs.bucket_arn}/*",
                                self.athena_result_bucket.bucket.bucket_arn,
                                f"{self.athena_result_bucket.bucket.bucket_arn}/*",
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
                                app_sync_athena_data_source_construct_inputs.glue_schema_arn,
                                Stack.of(self).format_arn(
                                    service="glue",
                                    resource="registry",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                    resource_name=app_sync_athena_data_source_construct_inputs.glue_registry_name,
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
                                    resource_name=app_sync_athena_data_source_construct_inputs.glue_database_name,
                                ),
                                Stack.of(self).format_arn(
                                    service="glue",
                                    resource="table",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                    resource_name=f"{app_sync_athena_data_source_construct_inputs.glue_database_name}/{app_sync_athena_data_source_construct_inputs.glue_table_name}",
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
                "ec2-vpc-policy": generate_ec2_vpc_policy(
                    self,
                    vpc_construct=app_sync_athena_data_source_construct_inputs.vpc_construct,
                    subnet_selection=app_sync_athena_data_source_construct_inputs.vpc_construct.private_subnet_selection,
                    authorized_service="lambda.amazonaws.com",
                ),
            },
        )

        athena_data_source_lambda = aws_lambda.Function(
            self,
            "lambda",
            function_name=athena_data_source_lambda_name,
            code=aws_lambda.Code.from_asset(
                "deployment/dist/lambda/athena_data_source.zip"
            ),
            description="CMS API Athena data source Lambda",
            handler="function.main.handler",
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            layers=[app_sync_athena_data_source_construct_inputs.dependency_layer],
            vpc=app_sync_athena_data_source_construct_inputs.vpc_construct.vpc,
            vpc_subnets=app_sync_athena_data_source_construct_inputs.vpc_construct.private_subnet_selection,
            security_groups=[
                aws_ec2.SecurityGroup(
                    self,
                    "security-group",
                    vpc=app_sync_athena_data_source_construct_inputs.vpc_construct.vpc,
                    allow_all_outbound=True,  # NOSONAR
                )
            ],
            role=athena_data_source_lambda_role,
            timeout=Duration.minutes(1),
            environment={
                # meta environmental variables
                "USER_AGENT_STRING": solution_config_inputs.get_user_agent_string(),
                "SOLUTION_ID": solution_config_inputs.solution_id,
                "SOLUTION_VERSION": solution_config_inputs.solution_version,
                "AWS_ACCOUNT_ID": Stack.of(self).account,
                "METRICS_SOLUTION_URL": app_sync_athena_data_source_construct_inputs.metrics_url,
                "REPORT_METRICS_ENABLED": app_sync_athena_data_source_construct_inputs.report_metrics_enabled,
                "DEPLOYMENT_UUID": app_sync_athena_data_source_construct_inputs.deployment_uuid,
                # functional environmental variables
                "GLUE_DATABASE_NAME": app_sync_athena_data_source_construct_inputs.glue_database_name,
                "GLUE_TABLE_NAME": app_sync_athena_data_source_construct_inputs.glue_table_name,
                "ATHENA_WORKGROUP": self.athena_workgroup.name,
                "RECORD_LIMIT": "100",
            },
        )

        athena_data_source = app_sync_athena_data_source_construct_inputs.appsync_api.add_lambda_data_source(
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
