# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from dataclasses import dataclass

# Third Party Libraries
from aws_cdk import CfnOutput, Stack, aws_ssm
from constructs import Construct

# Connected Mobility Solution on AWS
from ...config.constants import APIConstants


@dataclass(frozen=True)
class OperationalMetricsInput:
    metrics_url: str
    report_metrics_enabled: str
    deployment_uuid: str


@dataclass(frozen=True)
class GlueInputs:
    database_name: str
    table_name: str
    schema_arn: str
    registry_name: str


@dataclass(frozen=True)
class RootBucketInputs:
    bucket_arn: str
    bucket_key_arn: str


@dataclass(frozen=True)
class TokenValidationInputs:
    lambda_arn: str


class ModuleInputsConstruct(Construct):
    def __init__(self, scope: Construct, construct_id: str) -> None:
        super().__init__(scope, construct_id)
        self.operational_metrics = OperationalMetricsInput(
            metrics_url=aws_ssm.StringParameter.from_string_parameter_attributes(
                self,
                "ssm-operational-metrics-url",
                parameter_name=f"/{APIConstants.STAGE}/common/metrics/url",
            ).string_value,
            report_metrics_enabled=aws_ssm.StringParameter.from_string_parameter_attributes(
                self,
                "ssm-operational-report-metrics-enabled",
                parameter_name=f"/{APIConstants.STAGE}/common/metrics/enabled",
            ).string_value,
            deployment_uuid=aws_ssm.StringParameter.from_string_parameter_attributes(
                self,
                "ssm-deployment-uuid",
                parameter_name=f"/{APIConstants.STAGE}/cms/common/config/deployment-uuid",
            ).string_value,
        )
        self.glue = GlueInputs(
            database_name=aws_ssm.StringParameter.from_string_parameter_attributes(
                self,
                "ssm-glue-database-name",
                parameter_name=f"/{APIConstants.STAGE}/cms/telemetry/glue-database/name",
            ).string_value,
            table_name=aws_ssm.StringParameter.from_string_parameter_attributes(
                self,
                "ssm-glue-table-name",
                parameter_name=f"/{APIConstants.STAGE}/cms/telemetry/glue-table/name",
            ).string_value,
            schema_arn=aws_ssm.StringParameter.from_string_parameter_attributes(
                self,
                "ssm-glue-schema-arn",
                parameter_name=f"/{APIConstants.STAGE}/cms/telemetry/glue-schema/arn",
            ).string_value,
            registry_name=aws_ssm.StringParameter.from_string_parameter_attributes(
                self,
                "ssm-glue-registry-name",
                parameter_name=f"/{APIConstants.STAGE}/cms/telemetry/glue-registry/name",
            ).string_value,
        )
        self.root_bucket = RootBucketInputs(
            bucket_arn=aws_ssm.StringParameter.from_string_parameter_attributes(
                self,
                "ssm-root-bucket-arn",
                parameter_name=f"/{APIConstants.STAGE}/cms/telemetry/s3-storage-bucket/arn",
            ).string_value,
            bucket_key_arn=aws_ssm.StringParameter.from_string_parameter_attributes(
                self,
                "ssm-root-key-arn",
                parameter_name=f"/{APIConstants.STAGE}/cms/telemetry/s3-storage-bucket/key-arn",
            ).string_value,
        )
        self.token_validation = TokenValidationInputs(
            lambda_arn=aws_ssm.StringParameter.from_string_parameter_attributes(
                self,
                "ssm-token-validation-lambda-arn",
                parameter_name=f"/{APIConstants.STAGE}/cms/authentication/token-validation-lambda/arn",
            ).string_value
        )


class ModuleOutputsConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        athena_result_bucket_name: str,
        athena_result_bucket_arn: str,
        athena_result_bucket_key_arn: str,
        athena_workgroup_name: str,
        appsync_graphql_url: str,
    ) -> None:
        super().__init__(scope, construct_id)

        # SSM Parameters
        self.athena_result_bucket_name = aws_ssm.StringParameter(
            self,
            "ssm-athena-result-bucket-name",
            string_value=athena_result_bucket_name,
            description="Name of S3 bucket where Athena results are stored",
            parameter_name=f"/{APIConstants.STAGE}/cms/api/athena-result-bucket/name",
        )
        self.athena_result_bucket_arn = aws_ssm.StringParameter(
            self,
            "ssm-athena-result-bucket-arn",
            string_value=athena_result_bucket_arn,
            description="Arn of S3 bucket where Athena results are stored",
            parameter_name=f"/{APIConstants.STAGE}/cms/api/athena-result-bucket/arn",
        )
        self.athena_result_bucket_region = aws_ssm.StringParameter(
            self,
            "ssm-athena-result-bucket-region",
            string_value=Stack.of(self).region,
            description="Region of S3 bucket where Athena results are stored",
            parameter_name=f"/{APIConstants.STAGE}/cms/api/athena-result-bucket/region",
        )
        self.athena_result_bucket_key_arn = aws_ssm.StringParameter(
            self,
            "ssm-athena-result-bucket-key-arn",
            string_value=athena_result_bucket_key_arn,
            description="Arn of KMS key for S3 bucket where Athena results are stored",
            parameter_name=f"/{APIConstants.STAGE}/cms/api/athena-result-bucket/key-arn",
        )
        self.athena_workgroup_name = aws_ssm.StringParameter(
            self,
            "ssm-athena-workgroup-name",
            string_value=athena_workgroup_name,
            description="Name of Athena workgroup",
            parameter_name=f"/{APIConstants.STAGE}/cms/api/athena-workgroup/name",
        )
        self.appsync_graphql_url = aws_ssm.StringParameter(
            self,
            "ssm-graphql-endpoint-url",
            string_value=appsync_graphql_url,
            description="Endpoint URL for the CMS GraphQL API",
            parameter_name=f"/{APIConstants.STAGE}/cms/api/graphql-endpoint/url",
        )

        # Cfn Outputs
        CfnOutput(
            self,
            "output-graphql-endpoint-url",
            description="Endpoint URL for the CMS GraphQL API",
            value=appsync_graphql_url,
        )
