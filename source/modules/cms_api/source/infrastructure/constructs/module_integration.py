# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from dataclasses import dataclass

# AWS Libraries
from aws_cdk import CfnOutput, Stack, aws_ssm
from constructs import Construct

# CMS Common Library
from cms_common.config.metrics import OperationalMetricsInput
from cms_common.config.resource_names import ResourceName, ResourcePrefix
from cms_common.config.ssm import resolve_ssm_parameter
from cms_common.config.stack_inputs import SolutionConfigInputs
from cms_common.constructs.app_unique_id import AppUniqueId
from cms_common.constructs.vpc_construct import create_vpc_config, get_vpc_name
from cms_common.resource_names.module_short_names import CMSModuleShortNames


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
        self.app_unique_id = AppUniqueId.create_cfn_parameter(Stack.of(self))

        self.vpc_config = create_vpc_config(
            vpc_name=get_vpc_name(self, app_unique_id=self.app_unique_id)
        )
        self.operational_metrics = OperationalMetricsInput.from_app_unique_id(
            app_unique_id=self.app_unique_id
        )

        connect_store_module_ssm_prefix_with_leading_slash = (
            ResourcePrefix.slash_separated(
                app_unique_id=self.app_unique_id,
                module_name=CMSModuleShortNames.CONNECT_STORE,
                leading_slash=True,
            )
        )
        self.glue = GlueInputs(
            database_name=resolve_ssm_parameter(
                parameter_name=ResourceName.slash_separated(
                    prefix=connect_store_module_ssm_prefix_with_leading_slash,
                    name="glue-database/name",
                )
            ),
            table_name=resolve_ssm_parameter(
                parameter_name=ResourceName.slash_separated(
                    prefix=connect_store_module_ssm_prefix_with_leading_slash,
                    name="glue-table/name",
                )
            ),
            schema_arn=resolve_ssm_parameter(
                parameter_name=ResourceName.slash_separated(
                    prefix=connect_store_module_ssm_prefix_with_leading_slash,
                    name="glue-schema/arn",
                )
            ),
            registry_name=resolve_ssm_parameter(
                parameter_name=ResourceName.slash_separated(
                    prefix=connect_store_module_ssm_prefix_with_leading_slash,
                    name="glue-registry/name",
                )
            ),
        )
        self.root_bucket = RootBucketInputs(
            bucket_arn=resolve_ssm_parameter(
                parameter_name=ResourceName.slash_separated(
                    prefix=connect_store_module_ssm_prefix_with_leading_slash,
                    name="s3-storage-bucket/arn",
                )
            ),
            bucket_key_arn=resolve_ssm_parameter(
                parameter_name=ResourceName.slash_separated(
                    prefix=connect_store_module_ssm_prefix_with_leading_slash,
                    name="s3-storage-bucket/key-arn",
                )
            ),
        )

        auth_module_ssm_prefix_with_leading_slash = ResourcePrefix.slash_separated(
            app_unique_id=self.app_unique_id,
            module_name=CMSModuleShortNames.AUTH,
            leading_slash=True,
        )
        self.token_validation = TokenValidationInputs(
            lambda_arn=resolve_ssm_parameter(
                parameter_name=ResourceName.slash_separated(
                    prefix=auth_module_ssm_prefix_with_leading_slash,
                    name="token-validation-lambda/arn",
                )
            ),
        )


class ModuleOutputsConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_unique_id: str,
        solution_config_inputs: SolutionConfigInputs,
        athena_result_bucket_name: str,
        athena_result_bucket_arn: str,
        athena_result_bucket_key_arn: str,
        athena_workgroup_name: str,
        appsync_graphql_url: str,
    ) -> None:
        super().__init__(scope, construct_id)

        ssm_parameter_name_prefix = ResourcePrefix.slash_separated(
            app_unique_id=app_unique_id,
            module_name=solution_config_inputs.module_short_name,
            leading_slash=True,
        )

        # SSM Parameters
        self.athena_result_bucket_name = aws_ssm.StringParameter(
            self,
            "ssm-athena-result-bucket-name",
            string_value=athena_result_bucket_name,
            description="Name of S3 bucket where Athena results are stored",
            parameter_name=ResourceName.slash_separated(
                prefix=ssm_parameter_name_prefix, name="athena-result-bucket/name"
            ),
            simple_name=False,
        )
        self.athena_result_bucket_arn = aws_ssm.StringParameter(
            self,
            "ssm-athena-result-bucket-arn",
            string_value=athena_result_bucket_arn,
            description="Arn of S3 bucket where Athena results are stored",
            parameter_name=ResourceName.slash_separated(
                prefix=ssm_parameter_name_prefix, name="athena-result-bucket/arn"
            ),
            simple_name=False,
        )
        self.athena_result_bucket_region = aws_ssm.StringParameter(
            self,
            "ssm-athena-result-bucket-region",
            string_value=Stack.of(self).region,
            description="Region of S3 bucket where Athena results are stored",
            parameter_name=ResourceName.slash_separated(
                prefix=ssm_parameter_name_prefix, name="athena-result-bucket/region"
            ),
            simple_name=False,
        )
        self.athena_result_bucket_key_arn = aws_ssm.StringParameter(
            self,
            "ssm-athena-result-bucket-key-arn",
            string_value=athena_result_bucket_key_arn,
            description="Arn of KMS key for S3 bucket where Athena results are stored",
            parameter_name=ResourceName.slash_separated(
                prefix=ssm_parameter_name_prefix, name="athena-result-bucket/key-arn"
            ),
            simple_name=False,
        )
        self.athena_workgroup_name = aws_ssm.StringParameter(
            self,
            "ssm-athena-workgroup-name",
            string_value=athena_workgroup_name,
            description="Name of Athena workgroup",
            parameter_name=ResourceName.slash_separated(
                prefix=ssm_parameter_name_prefix, name="athena-workgroup/name"
            ),
            simple_name=False,
        )
        self.appsync_graphql_url = aws_ssm.StringParameter(
            self,
            "ssm-graphql-endpoint-url",
            string_value=appsync_graphql_url,
            description="Endpoint URL for the CMS GraphQL API",
            parameter_name=ResourceName.slash_separated(
                prefix=ssm_parameter_name_prefix, name="graphql-endpoint/url"
            ),
            simple_name=False,
        )

        # Cfn Outputs
        CfnOutput(
            self,
            "output-graphql-endpoint-url",
            description="Endpoint URL for the CMS GraphQL API",
            value=appsync_graphql_url,
        )
