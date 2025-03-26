# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from dataclasses import dataclass

# AWS Libraries
from aws_cdk import Stack, aws_ssm
from constructs import Construct

# CMS Common Library
from cms_common.config.resource_names import ResourceName, ResourcePrefix
from cms_common.config.ssm import resolve_ssm_parameter
from cms_common.config.stack_inputs import SolutionConfigInputs
from cms_common.constructs.app_unique_id import AppUniqueId
from cms_common.constructs.encrypted_s3 import EncryptedS3Construct
from cms_common.constructs.identity_provider_config import IdentityProviderConfig
from cms_common.constructs.vpc_construct import create_vpc_config, get_vpc_name
from cms_common.resource_names.module_short_names import CMSModuleShortNames


@dataclass(frozen=True)
class AthenaDataSourceProperties:
    athena_data_storage_bucket_arn: str
    athena_workgroup_name: str
    athena_results_bucket_arn: str
    glue_catalog_name: str
    glue_database_name: str
    glue_table_name: str
    glue_registry_name: str
    glue_schema_arn: str


class ModuleInputsConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
    ) -> None:
        super().__init__(scope, construct_id)

        self.app_unique_id = AppUniqueId.create_cfn_parameter(Stack.of(self))

        self.identity_provider_id = IdentityProviderConfig.get_identity_provider_id(
            scope=self, app_unique_id=self.app_unique_id
        )

        self.vpc_config = create_vpc_config(
            vpc_name=get_vpc_name(self, app_unique_id=self.app_unique_id)
        )

        alerts_module_ssm_prefix_with_leading_slash = ResourcePrefix.slash_separated(
            app_unique_id=self.app_unique_id,
            module_name=CMSModuleShortNames.ALERTS,
            leading_slash=True,
        )
        api_module_ssm_prefix_with_leading_slash = ResourcePrefix.slash_separated(
            app_unique_id=self.app_unique_id,
            module_name=CMSModuleShortNames.API,
            leading_slash=True,
        )
        connect_store_module_ssm_prefix_with_leading_slash = (
            ResourcePrefix.slash_separated(
                app_unique_id=self.app_unique_id,
                module_name=CMSModuleShortNames.CONNECT_STORE,
                leading_slash=True,
            )
        )

        self.athena_data_source_properties = AthenaDataSourceProperties(
            athena_workgroup_name=resolve_ssm_parameter(
                parameter_name=ResourceName.slash_separated(
                    prefix=api_module_ssm_prefix_with_leading_slash,
                    name="athena-workgroup/name",
                )
            ),
            athena_results_bucket_arn=resolve_ssm_parameter(
                parameter_name=ResourceName.slash_separated(
                    prefix=api_module_ssm_prefix_with_leading_slash,
                    name="athena-result-bucket/arn",
                )
            ),
            athena_data_storage_bucket_arn=resolve_ssm_parameter(
                parameter_name=ResourceName.slash_separated(
                    prefix=connect_store_module_ssm_prefix_with_leading_slash,
                    name="s3-storage-bucket/arn",
                )
            ),
            glue_catalog_name=resolve_ssm_parameter(
                parameter_name=ResourceName.slash_separated(
                    prefix=connect_store_module_ssm_prefix_with_leading_slash,
                    name="glue-data-catalog/name",
                )
            ),
            glue_database_name=resolve_ssm_parameter(
                parameter_name=ResourceName.slash_separated(
                    prefix=connect_store_module_ssm_prefix_with_leading_slash,
                    name="glue-database/name",
                )
            ),
            glue_registry_name=resolve_ssm_parameter(
                parameter_name=ResourceName.slash_separated(
                    prefix=connect_store_module_ssm_prefix_with_leading_slash,
                    name="glue-registry/name",
                )
            ),
            glue_schema_arn=resolve_ssm_parameter(
                parameter_name=ResourceName.slash_separated(
                    prefix=connect_store_module_ssm_prefix_with_leading_slash,
                    name="glue-schema/arn",
                )
            ),
            glue_table_name=resolve_ssm_parameter(
                parameter_name=ResourceName.slash_separated(
                    prefix=connect_store_module_ssm_prefix_with_leading_slash,
                    name="glue-table/name",
                )
            ),
        )

        self.alerts_publish_endpoint_url = resolve_ssm_parameter(
            parameter_name=ResourceName.slash_separated(
                prefix=alerts_module_ssm_prefix_with_leading_slash,
                name="publish-api/endpoint",
            )
        )

        self.s3_log_lifecycle_rules = (
            EncryptedS3Construct.create_log_lifecycle_cfn_parameters(self)
        )


class ModuleOutputsConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_unique_id: str,
        solution_config_inputs: SolutionConfigInputs,
        grafana_endpoint: str,
    ) -> None:
        super().__init__(scope, construct_id)

        ssm_parameter_name_prefix_with_leading_slash = ResourcePrefix.slash_separated(
            app_unique_id=app_unique_id,
            module_name=solution_config_inputs.module_short_name,
            leading_slash=True,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-grafana-endpoint",
            string_value=grafana_endpoint,
            description="EV Battery Health Dashboard Grafana Endpoint",
            parameter_name=ResourceName.slash_separated(
                prefix=ssm_parameter_name_prefix_with_leading_slash,
                name="grafana-workspace-endpoint/url",
            ),
            simple_name=False,
        )
