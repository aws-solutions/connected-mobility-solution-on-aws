# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from dataclasses import dataclass
from typing import Optional

# AWS Libraries
from aws_cdk import CfnParameter, Stack, aws_ssm
from constructs import Construct

# Connected Mobility Solution on AWS
from ..lib.cms_common.config.resource_names import ResourceName, ResourcePrefix
from ..lib.cms_common.config.stack_inputs import SolutionConfigInputs
from ..lib.cms_common.constructs.vpc_construct import create_vpc_config


@dataclass(frozen=True)
class AdminUserProperties:
    email: str
    username: str


@dataclass(frozen=True)
class BackstageConfigurationProperties:
    ecr_repository_name: str
    node_env: str
    log_level: str
    user_agent_string: str


@dataclass(frozen=True)
class AcdpAssetProperties:
    regional_asset_bucket_name: str
    local_asset_bucket_name: str
    local_asset_bucket_key_arn: str
    local_asset_bucket_root_key: str
    local_asset_bucket_default_assets_prefix: str


@dataclass(frozen=True)
class BackstageTaskDefinitionSecrets:
    backstage_name: aws_ssm.IStringParameter
    backstage_org: aws_ssm.IStringParameter
    regional_asset_bucket_name: aws_ssm.IStringParameter
    regional_asset_bucket_region: aws_ssm.IStringParameter
    regional_asset_bucket_template_key_prefix: aws_ssm.IStringParameter
    regional_asset_bucket_buildspec_key_prefix: aws_ssm.IStringParameter
    regional_asset_bucket_discovery_refresh_frequency: aws_ssm.IStringParameter
    local_asset_bucket_name: aws_ssm.IStringParameter
    local_asset_bucket_region: aws_ssm.IStringParameter
    local_asset_bucket_kms_key_arn: aws_ssm.IStringParameter
    local_asset_bucket_root_key_parameter: aws_ssm.IStringParameter
    local_asset_bucket_default_assets_prefix_parameter: aws_ssm.IStringParameter
    local_asset_bucket_backstage_user_provided_template_key_prefix: aws_ssm.IStringParameter
    local_asset_bucket_backstage_default_template_key_prefix: aws_ssm.IStringParameter
    local_asset_bucket_catalog_key_prefix: aws_ssm.IStringParameter
    local_asset_bucket_techdocs_key_prefix: aws_ssm.IStringParameter
    local_asset_bucket_discovery_refresh_frequency_mins: aws_ssm.IStringParameter
    codebuild_project_arn: aws_ssm.IStringParameter
    acdp_build_config_path_root_parameter: aws_ssm.IStringParameter


class SsmParameterWithAndWithoutSlashPrefix(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        path_prefix_with_slash: str,
        path_prefix_without_slash: str,
        path_postfix: str,
        create_parameter: bool = False,
        create_parameter_value: Optional[str] = None,
        create_parameter_description: Optional[str] = None,
    ) -> None:
        super().__init__(scope, construct_id)

        if create_parameter:
            if create_parameter_value is None:
                raise ValueError(
                    "create_parameter_value must be set when creating a parameter"
                )
            new_parameter = aws_ssm.StringParameter(
                self,
                "create-ssm-param",
                string_value=create_parameter_value,
                description=create_parameter_description,
                parameter_name=ResourceName.slash_separated(
                    prefix=path_prefix_with_slash,
                    name=path_postfix,
                ),
                simple_name=True,
            )
            self.string_value = new_parameter.string_value
        else:
            parameter_with_slash_prefix = (
                aws_ssm.StringParameter.from_string_parameter_attributes(
                    self,
                    "ssm-param-with-slash-prefix",
                    parameter_name=ResourceName.slash_separated(
                        prefix=path_prefix_with_slash,
                        name=path_postfix,
                    ),
                    simple_name=True,
                    force_dynamic_reference=True,
                )
            )

            self.string_value = parameter_with_slash_prefix.string_value

        self.parameter_without_slash_prefix = (
            aws_ssm.StringParameter.from_string_parameter_attributes(
                self,
                "ssm-param-without-slash-prefix",
                parameter_name=ResourceName.slash_separated(
                    prefix=path_prefix_without_slash,
                    name=path_postfix,
                ),
                simple_name=True,
                force_dynamic_reference=True,
            )
        )


class ModuleInputsConstruct(Construct):
    # pylint: disable=R0914
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        solution_config_inputs: SolutionConfigInputs,
    ) -> None:
        super().__init__(scope, construct_id)

        self.acdp_uid = CfnParameter(
            Stack.of(self),
            "AcdpUniqueId",
            description="Name of the ACDP deployment",
            default="acdp",
            type="String",
        ).value_as_string

        self.vpc_name = CfnParameter(
            Stack.of(self),
            "VpcName",
            description="name of the imported vpc",
            type="String",
        ).value_as_string

        self.vpc_config = create_vpc_config(
            vpc_name=self.vpc_name,
        )

        self.acdp_config_ssm_prefix_with_slash_prefix = ResourcePrefix.slash_separated(
            app_unique_id=self.acdp_uid, module_name="config", leading_slash=True
        )

        self.acdp_config_ssm_prefix_without_slash_prefix = (
            ResourcePrefix.slash_separated(
                app_unique_id=self.acdp_uid, module_name="config", leading_slash=False
            )
        )

        self.acdp_build_ssm_prefix_with_slash_prefix = ResourcePrefix.slash_separated(
            app_unique_id=self.acdp_uid, module_name="acdp-build", leading_slash=True
        )

        self.acdp_build_ssm_prefix_without_slash_prefix = (
            ResourcePrefix.slash_separated(
                app_unique_id=self.acdp_uid,
                module_name="acdp-build",
                leading_slash=False,
            )
        )

        regional_asset_config_ssm_path = "acdp-asset-config/regional"
        local_asset_config_ssm_path = "acdp-asset-config/local"

        regional_asset_bucket_name_parameter = SsmParameterWithAndWithoutSlashPrefix(
            self,
            "ssm-regional-asset-bucket-name-parameter",
            path_prefix_with_slash=self.acdp_config_ssm_prefix_with_slash_prefix,
            path_prefix_without_slash=self.acdp_config_ssm_prefix_without_slash_prefix,
            path_postfix=f"{regional_asset_config_ssm_path}/asset-bucket/name",
        )

        regional_asset_bucket_region_parameter = SsmParameterWithAndWithoutSlashPrefix(
            self,
            "ssm-regional-asset-bucket-region-parameter",
            path_prefix_with_slash=self.acdp_config_ssm_prefix_with_slash_prefix,
            path_prefix_without_slash=self.acdp_config_ssm_prefix_without_slash_prefix,
            path_postfix=f"{regional_asset_config_ssm_path}/asset-bucket/region",
        )

        regional_asset_bucket_template_key_prefix_parameter = SsmParameterWithAndWithoutSlashPrefix(
            self,
            "ssm-regional-asset-bucket-template-key-prefix-parameter",
            path_prefix_with_slash=self.acdp_config_ssm_prefix_with_slash_prefix,
            path_prefix_without_slash=self.acdp_config_ssm_prefix_without_slash_prefix,
            path_postfix=f"{regional_asset_config_ssm_path}/backstage-template-key-prefix",
        )

        regional_asset_bucket_buildspec_key_prefix_parameter = SsmParameterWithAndWithoutSlashPrefix(
            self,
            "ssm-regional-asset-bucket-buildspec-key-prefix-parameter",
            path_prefix_with_slash=self.acdp_config_ssm_prefix_with_slash_prefix,
            path_prefix_without_slash=self.acdp_config_ssm_prefix_without_slash_prefix,
            path_postfix=f"{regional_asset_config_ssm_path}/buildspec-key-prefix",
        )

        regional_asset_bucket_discovery_refresh_frequency_mins_parameter = SsmParameterWithAndWithoutSlashPrefix(
            self,
            "ssm-regional-asset-bucket-refresh-frequency-mins-parameter",
            path_prefix_with_slash=self.acdp_config_ssm_prefix_with_slash_prefix,
            path_prefix_without_slash=self.acdp_config_ssm_prefix_without_slash_prefix,
            path_postfix=f"{regional_asset_config_ssm_path}/discovery-refresh-frequency-mins",
        )

        local_asset_bucket_name_parameter = SsmParameterWithAndWithoutSlashPrefix(
            self,
            "ssm-local-asset-bucket-name-parameter",
            path_prefix_with_slash=self.acdp_config_ssm_prefix_with_slash_prefix,
            path_prefix_without_slash=self.acdp_config_ssm_prefix_without_slash_prefix,
            path_postfix=f"{local_asset_config_ssm_path}/asset-bucket/name",
        )

        local_asset_bucket_kms_key_arn_parameter = SsmParameterWithAndWithoutSlashPrefix(
            self,
            "ssm-local-asset-config-bucket-key-arn",
            path_prefix_with_slash=self.acdp_config_ssm_prefix_with_slash_prefix,
            path_prefix_without_slash=self.acdp_config_ssm_prefix_without_slash_prefix,
            path_postfix=f"{local_asset_config_ssm_path}/asset-bucket/key-arn",
        )

        local_asset_bucket_region_parameter = SsmParameterWithAndWithoutSlashPrefix(
            self,
            "ssm-local-asset-bucket-region-parameter",
            path_prefix_with_slash=self.acdp_config_ssm_prefix_with_slash_prefix,
            path_prefix_without_slash=self.acdp_config_ssm_prefix_without_slash_prefix,
            path_postfix=f"{local_asset_config_ssm_path}/asset-bucket/region",
        )

        local_asset_bucket_root_key_parameter = SsmParameterWithAndWithoutSlashPrefix(
            self,
            "ssm-local-asset-config-asset-bucket-root-key",
            path_prefix_with_slash=self.acdp_config_ssm_prefix_with_slash_prefix,
            path_prefix_without_slash=self.acdp_config_ssm_prefix_without_slash_prefix,
            path_postfix=f"{local_asset_config_ssm_path}/root-s3-key",
        )

        local_asset_bucket_default_assets_prefix_parameter = SsmParameterWithAndWithoutSlashPrefix(
            self,
            "ssm-local-asset-config-asset-default-assets-prefix",
            path_prefix_with_slash=self.acdp_config_ssm_prefix_with_slash_prefix,
            path_prefix_without_slash=self.acdp_config_ssm_prefix_without_slash_prefix,
            path_postfix=f"{local_asset_config_ssm_path}/default-assets-prefix",
        )

        local_asset_bucket_custom_template_key_prefix_parameter = SsmParameterWithAndWithoutSlashPrefix(
            self,
            "ssm-local-asset-config-asset-bucket-backstage-custom-template-key-prefix",
            path_prefix_with_slash=self.acdp_config_ssm_prefix_with_slash_prefix,
            path_prefix_without_slash=self.acdp_config_ssm_prefix_without_slash_prefix,
            path_postfix=f"{local_asset_config_ssm_path}/backstage-custom-template-key-prefix",
        )

        local_asset_bucket_default_template_key_prefix_parameter = SsmParameterWithAndWithoutSlashPrefix(
            self,
            "ssm-local-asset-config-asset-bucket-backstage-default-template-key-prefix",
            path_prefix_with_slash=self.acdp_config_ssm_prefix_with_slash_prefix,
            path_prefix_without_slash=self.acdp_config_ssm_prefix_without_slash_prefix,
            path_postfix=f"{local_asset_config_ssm_path}/backstage-default-template-key-prefix",
        )

        local_asset_bucket_catalog_key_prefix_parameter = SsmParameterWithAndWithoutSlashPrefix(
            self,
            "ssm-local-asset-config-asset-bucket-catalog-key-prefix",
            path_prefix_with_slash=self.acdp_config_ssm_prefix_with_slash_prefix,
            path_prefix_without_slash=self.acdp_config_ssm_prefix_without_slash_prefix,
            path_postfix=f"{local_asset_config_ssm_path}/catalog-key-prefix",
        )

        local_asset_bucket_techdocs_key_prefix_parameter = SsmParameterWithAndWithoutSlashPrefix(
            self,
            "ssm-local-asset-config-asset-bucket-techdocs-key-prefix",
            path_prefix_with_slash=self.acdp_config_ssm_prefix_with_slash_prefix,
            path_prefix_without_slash=self.acdp_config_ssm_prefix_without_slash_prefix,
            path_postfix=f"{local_asset_config_ssm_path}/techdocs-key-prefix",
        )

        local_asset_bucket_discovery_refresh_frequency_mins_parameter = SsmParameterWithAndWithoutSlashPrefix(
            self,
            "ssm-local-asset-config-backstage-discovery-refresh-freq-mins",
            path_prefix_with_slash=self.acdp_config_ssm_prefix_with_slash_prefix,
            path_prefix_without_slash=self.acdp_config_ssm_prefix_without_slash_prefix,
            path_postfix=f"{local_asset_config_ssm_path}/discovery-refresh-frequency-mins",
        )

        codebuild_project_arn_parameter = SsmParameterWithAndWithoutSlashPrefix(
            self,
            "ssm-codebuild-project-arn-parameter",
            path_prefix_with_slash=self.acdp_config_ssm_prefix_with_slash_prefix,
            path_prefix_without_slash=self.acdp_config_ssm_prefix_without_slash_prefix,
            path_postfix="codebuild-project/arn",
        )

        backstage_name_parameter = SsmParameterWithAndWithoutSlashPrefix(
            self,
            "ssm-backstage-name-parameter",
            path_prefix_with_slash=self.acdp_config_ssm_prefix_with_slash_prefix,
            path_prefix_without_slash=self.acdp_config_ssm_prefix_without_slash_prefix,
            path_postfix="backstage/name",
        )

        backstage_org_parameter = SsmParameterWithAndWithoutSlashPrefix(
            self,
            "ssm-backstage-org-parameter",
            path_prefix_with_slash=self.acdp_config_ssm_prefix_with_slash_prefix,
            path_prefix_without_slash=self.acdp_config_ssm_prefix_without_slash_prefix,
            path_postfix="backstage/organization",
        )

        backstage_ecr_repository_name_parameter = SsmParameterWithAndWithoutSlashPrefix(
            self,
            "ssm-backstage-ecr-repository-name",
            path_prefix_with_slash=self.acdp_config_ssm_prefix_with_slash_prefix,
            path_prefix_without_slash=self.acdp_config_ssm_prefix_without_slash_prefix,
            path_postfix="backstage/ecr-repository/name",
        )

        backstage_log_level_parameter = SsmParameterWithAndWithoutSlashPrefix(
            self,
            "ssm-backstage-log-level",
            path_prefix_with_slash=self.acdp_config_ssm_prefix_with_slash_prefix,
            path_prefix_without_slash=self.acdp_config_ssm_prefix_without_slash_prefix,
            path_postfix="backstage/log-level",
        )

        backstage_admin_email_parameter = SsmParameterWithAndWithoutSlashPrefix(
            self,
            "ssm-backstage-admin-email",
            path_prefix_with_slash=self.acdp_config_ssm_prefix_with_slash_prefix,
            path_prefix_without_slash=self.acdp_config_ssm_prefix_without_slash_prefix,
            path_postfix="backstage/admin-email",
        )

        acdp_build_config_path_root_parameter = SsmParameterWithAndWithoutSlashPrefix(
            self,
            "ssm-acdp-build-ssm-prefix",
            path_prefix_with_slash=self.acdp_build_ssm_prefix_with_slash_prefix,
            path_prefix_without_slash=self.acdp_build_ssm_prefix_without_slash_prefix,
            path_postfix="build-parameters",
            create_parameter=True,
            create_parameter_value=self.acdp_build_ssm_prefix_with_slash_prefix,
        )

        backstage_admin_username_parameter = SsmParameterWithAndWithoutSlashPrefix(
            self,
            "ssm-backstage-admin-username",
            path_prefix_with_slash=self.acdp_config_ssm_prefix_with_slash_prefix,
            path_prefix_without_slash=self.acdp_config_ssm_prefix_without_slash_prefix,
            path_postfix="backstage/admin-username",
        )

        self.acdp_asset_properties = AcdpAssetProperties(
            regional_asset_bucket_name=regional_asset_bucket_name_parameter.string_value,
            local_asset_bucket_name=local_asset_bucket_name_parameter.string_value,
            local_asset_bucket_key_arn=local_asset_bucket_kms_key_arn_parameter.string_value,
            local_asset_bucket_root_key=local_asset_bucket_root_key_parameter.string_value,
            local_asset_bucket_default_assets_prefix=local_asset_bucket_default_assets_prefix_parameter.string_value,
        )

        self.backstage_configuration = BackstageConfigurationProperties(
            ecr_repository_name=backstage_ecr_repository_name_parameter.string_value,
            node_env="production",
            log_level=backstage_log_level_parameter.string_value,
            user_agent_string=solution_config_inputs.get_user_agent_string(),
        )

        self.admin_user = AdminUserProperties(
            email=backstage_admin_email_parameter.string_value,
            username=backstage_admin_username_parameter.string_value,
        )

        self.backstage_task_definition_secrets = BackstageTaskDefinitionSecrets(
            backstage_name=backstage_name_parameter.parameter_without_slash_prefix,
            backstage_org=backstage_org_parameter.parameter_without_slash_prefix,
            regional_asset_bucket_name=regional_asset_bucket_name_parameter.parameter_without_slash_prefix,
            regional_asset_bucket_region=regional_asset_bucket_region_parameter.parameter_without_slash_prefix,
            regional_asset_bucket_template_key_prefix=regional_asset_bucket_template_key_prefix_parameter.parameter_without_slash_prefix,
            regional_asset_bucket_buildspec_key_prefix=regional_asset_bucket_buildspec_key_prefix_parameter.parameter_without_slash_prefix,
            regional_asset_bucket_discovery_refresh_frequency=regional_asset_bucket_discovery_refresh_frequency_mins_parameter.parameter_without_slash_prefix,
            local_asset_bucket_name=local_asset_bucket_name_parameter.parameter_without_slash_prefix,
            local_asset_bucket_region=local_asset_bucket_region_parameter.parameter_without_slash_prefix,
            local_asset_bucket_kms_key_arn=local_asset_bucket_kms_key_arn_parameter.parameter_without_slash_prefix,
            local_asset_bucket_root_key_parameter=local_asset_bucket_root_key_parameter.parameter_without_slash_prefix,
            local_asset_bucket_default_assets_prefix_parameter=local_asset_bucket_default_assets_prefix_parameter.parameter_without_slash_prefix,
            local_asset_bucket_backstage_user_provided_template_key_prefix=local_asset_bucket_custom_template_key_prefix_parameter.parameter_without_slash_prefix,
            local_asset_bucket_backstage_default_template_key_prefix=local_asset_bucket_default_template_key_prefix_parameter.parameter_without_slash_prefix,
            local_asset_bucket_catalog_key_prefix=local_asset_bucket_catalog_key_prefix_parameter.parameter_without_slash_prefix,
            local_asset_bucket_techdocs_key_prefix=local_asset_bucket_techdocs_key_prefix_parameter.parameter_without_slash_prefix,
            local_asset_bucket_discovery_refresh_frequency_mins=local_asset_bucket_discovery_refresh_frequency_mins_parameter.parameter_without_slash_prefix,
            codebuild_project_arn=codebuild_project_arn_parameter.parameter_without_slash_prefix,
            acdp_build_config_path_root_parameter=acdp_build_config_path_root_parameter.parameter_without_slash_prefix,
        )
