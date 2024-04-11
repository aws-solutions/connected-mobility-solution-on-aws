# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Union

# Third Party Libraries
from attrs import define

# AWS Libraries
from aws_cdk import CfnMapping, CfnParameter, Stack, aws_s3, aws_ssm
from constructs import Construct

# CMS Common Library
from cms_common.config.resource_names import ResourceName, ResourcePrefix
from cms_common.constructs.vpc_construct import create_vpc_config
from cms_common.resource_names.module_short_names import CMSModuleShortNames

# Connected Mobility Solution on AWS
from .cmk_encrypted_s3 import CMKEncryptedS3Construct

MINUTES_IN_A_DAY = 1440


@define(auto_attribs=True, frozen=True)
class BackstageS3RegionalAssetsConfigInputs:
    bucket_name: str
    bucket_region: str
    backstage_template_key_prefix: str
    buildspec_key_prefix: str
    discovery_refresh_frequency_mins: Union[int, float]


@define(auto_attribs=True, frozen=True)
class BackstageS3LocalAssetsConfigInputs:
    bucket: aws_s3.IBucket
    bucket_name: str
    bucket_region: str
    bucket_key_arn: str
    bucket_access_root_key: str
    backstage_default_assets_prefix: str
    backstage_user_provided_template_key_prefix: str
    backstage_default_template_key_prefix: str
    catalog_key_prefix: str
    techdocs_key_prefix: str
    discovery_refresh_frequency_mins: Union[int, float]


@define(auto_attribs=True, frozen=True)
class BackstageDomainInputs:
    route53_zone_name: str
    route53_base_domain_name: str


@define(auto_attribs=True, frozen=True)
class BackstageConfigInputs:
    name: str
    org: str
    log_level: str


class ModuleInputsConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        solution_mapping: CfnMapping,
        backstage_s3_assets_key_prefix: str,
        local_asset_bucket_construct: CMKEncryptedS3Construct,
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

        self.vpc_config = create_vpc_config(vpc_name=self.vpc_name)

        self.backstage_user_email = CfnParameter(
            Stack.of(self),
            "UserEmail",
            type="String",
            description="The user email to access Backstage",
            allowed_pattern=r"^[A-Za-z0-9][_A-Za-z0-9-\.]*@([A-Za-z0-9]+[_A-Za-z0-9-]*\.)+[A-Za-z]+$",
            constraint_description="User email must be a valid email address",
        ).value_as_string

        self.backstage_domain_inputs = BackstageDomainInputs(
            route53_zone_name=CfnParameter(
                Stack.of(self),
                "Route53ZoneName",
                type="String",
                description="Route53 Zone Name for Backstage Domain",
                allowed_pattern=r"^([A-Za-z0-9][A-Za-z0-9-]*\.)+[A-Za-z]+$",
                constraint_description="Route53 Zone Name must be a valid domain name",
            ).value_as_string,
            route53_base_domain_name=CfnParameter(
                Stack.of(self),
                "Route53BaseDomain",
                type="String",
                description="Route53 Base Domain Name for Backstage Domain",
                allowed_pattern=r"^([A-Za-z0-9][A-Za-z0-9-]*\.)+[A-Za-z]+$",
                constraint_description="Route53 Base Domain must be a valid domain name",
            ).value_as_string,
        )

        self.backstage_config_inputs = BackstageConfigInputs(
            name=CfnParameter(
                Stack.of(self),
                "BackstageName",
                type="String",
                description="Name to use for the Backstage Portal",
                default="ACDP",
                allowed_pattern=r"^[A-Za-z0-9][A-Za-z0-9-_ ]*[A-Za-z0-9]$",
                constraint_description="Backstage Name must begin and end with an alphanumeric character and only consist of alphanumeric characters, space, hyphen(-) and underscore(_)",
            ).value_as_string,
            org=CfnParameter(
                Stack.of(self),
                "BackstageOrg",
                type="String",
                description="Organization Name to use for the Backstage Portal",
                default="Auto",
                allowed_pattern=r"^[A-Za-z0-9][A-Za-z0-9-_ ]*[A-Za-z0-9]$",
                constraint_description="Backstage Org must begin and end with an alphanumeric character and only consist of alphanumeric characters, space, hyphen(-) and underscore(_)",
            ).value_as_string,
            log_level=CfnParameter(
                Stack.of(self),
                "BackstageLogLevel",
                type="String",
                description="Log-level to set for the Backstage resources",
                allowed_values=["debug", "info"],
                default="info",
            ).value_as_string,
        )

        self.regional_asset_bucket_inputs = BackstageS3RegionalAssetsConfigInputs(
            bucket_name=f'{solution_mapping.find_in_map("AssetsConfig", "S3AssetBucketBaseName")}-{Stack.of(self).region}',
            bucket_region=Stack.of(self).region,
            backstage_template_key_prefix=f"{backstage_s3_assets_key_prefix}/templates",
            buildspec_key_prefix=f"{backstage_s3_assets_key_prefix}/acdp",
            discovery_refresh_frequency_mins=MINUTES_IN_A_DAY,
        )

        backstage_local_asset_bucket_access_root_key = "backstage"
        backstage_local_asset_bucket_default_assets_prefix = "backstage-default-assets"
        self.local_asset_bucket_inputs = BackstageS3LocalAssetsConfigInputs(
            bucket=local_asset_bucket_construct.bucket,
            bucket_name=local_asset_bucket_construct.bucket.bucket_name,
            bucket_region=Stack.of(self).region,
            bucket_key_arn=local_asset_bucket_construct.key.key_arn,
            bucket_access_root_key=backstage_local_asset_bucket_access_root_key,
            backstage_default_assets_prefix=backstage_local_asset_bucket_default_assets_prefix,
            backstage_user_provided_template_key_prefix=f"{backstage_local_asset_bucket_access_root_key}/templates",
            backstage_default_template_key_prefix=f"{backstage_local_asset_bucket_default_assets_prefix}/templates",
            catalog_key_prefix=f"{backstage_local_asset_bucket_access_root_key}/catalog",
            techdocs_key_prefix=f"{backstage_local_asset_bucket_access_root_key}/techdocs",
            discovery_refresh_frequency_mins=CfnParameter(
                Stack.of(self),
                "BackstageLocalAssetDiscoveryRefreshMins",
                type="Number",
                description="Refresh Frequency (minutes) for Backstage catalog provider from the Backstage Local Asset Bucket",
                min_value=1,
                default=30,
            ).value_as_number,
        )

        self.acdp_config_ssm_prefix = ResourcePrefix.slash_separated(
            app_unique_id=self.acdp_uid,
            module_name=CMSModuleShortNames.CONFIG,
            leading_slash=True,
        )

        self.acdp_config_ssm_prefix_without_prefix_slash = (
            ResourcePrefix.slash_separated(
                app_unique_id=self.acdp_uid,
                module_name=CMSModuleShortNames.CONFIG,
                leading_slash=False,
            )
        )


class ModuleOutputsConstruct(Construct):
    # pylint: disable=too-many-arguments
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        deployment_uuid: str,
        backstage_regional_asset_config_inputs: BackstageS3RegionalAssetsConfigInputs,
        backstage_local_asset_bucket_config_inputs: BackstageS3LocalAssetsConfigInputs,
        codebuild_project_arn: str,
        acdp_config_ssm_prefix: str,
    ) -> None:
        super().__init__(scope, construct_id)

        regional_asset_config_ssm_path = "acdp-asset-config/regional"
        local_asset_config_ssm_path = "acdp-asset-config/local"

        aws_ssm.StringParameter(
            self,
            "ssm-acdp-deployment-uuid",
            string_value=deployment_uuid,
            description="Solution UUID used to tag resources within ACDP",
            parameter_name=ResourceName.slash_separated(
                prefix=acdp_config_ssm_prefix,
                name="deployment-uuid",
            ),
            simple_name=True,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-regional-asset-config-bucket-name",
            string_value=backstage_regional_asset_config_inputs.bucket_name,
            description="Name of the regional asset bucket where ACDP Deployable resources are discovered",
            parameter_name=ResourceName.slash_separated(
                prefix=acdp_config_ssm_prefix,
                name=f"{regional_asset_config_ssm_path}/asset-bucket/name",
            ),
            simple_name=True,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-regional-asset-config-bucket-region",
            string_value=backstage_regional_asset_config_inputs.bucket_region,
            description="Region of the regional bucket where ACDP Deployable resources are discovered",
            parameter_name=ResourceName.slash_separated(
                prefix=acdp_config_ssm_prefix,
                name=f"{regional_asset_config_ssm_path}/asset-bucket/region",
            ),
            simple_name=True,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-regional-asset-config-backstage-template-key-prefix",
            string_value=backstage_regional_asset_config_inputs.backstage_template_key_prefix,
            description="Bucket key prefix for the regional bucket where ACDP Deployable resources are discovered",
            parameter_name=ResourceName.slash_separated(
                prefix=acdp_config_ssm_prefix,
                name=f"{regional_asset_config_ssm_path}/backstage-template-key-prefix",
            ),
            simple_name=True,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-regional-asset-config-backstage-buildspec-key-prefix",
            string_value=backstage_regional_asset_config_inputs.buildspec_key_prefix,
            description="Bucket key prefix where ACDP BuildSpecs are to be accessed from",
            parameter_name=ResourceName.slash_separated(
                prefix=acdp_config_ssm_prefix,
                name=f"{regional_asset_config_ssm_path}/buildspec-key-prefix",
            ),
            simple_name=True,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-regional-asset-config-backstage-discovery-refresh-freq-mins",
            string_value=str(
                backstage_regional_asset_config_inputs.discovery_refresh_frequency_mins
            ),
            description="Frequency to allow refresh of Backstage catalog provider from the regional bucket",
            parameter_name=ResourceName.slash_separated(
                prefix=acdp_config_ssm_prefix,
                name=f"{regional_asset_config_ssm_path}/discovery-refresh-frequency-mins",
            ),
            simple_name=True,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-local-asset-config-bucket-name",
            string_value=backstage_local_asset_bucket_config_inputs.bucket_name,
            description="Name of the local asset bucket where ACDP Deployable resources are discovered",
            parameter_name=ResourceName.slash_separated(
                prefix=acdp_config_ssm_prefix,
                name=f"{local_asset_config_ssm_path}/asset-bucket/name",
            ),
            simple_name=True,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-local-asset-config-bucket-region",
            string_value=backstage_local_asset_bucket_config_inputs.bucket_region,
            description="Region of the local bucket where ACDP Deployable resources are discovered",
            parameter_name=ResourceName.slash_separated(
                prefix=acdp_config_ssm_prefix,
                name=f"{local_asset_config_ssm_path}/asset-bucket/region",
            ),
            simple_name=True,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-local-asset-config-bucket-key-arn",
            string_value=backstage_local_asset_bucket_config_inputs.bucket_key_arn,
            description="KMS Key ARN of the local asset bucket",
            parameter_name=ResourceName.slash_separated(
                prefix=acdp_config_ssm_prefix,
                name=f"{local_asset_config_ssm_path}/asset-bucket/key-arn",
            ),
            simple_name=True,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-local-asset-config-asset-bucket-root-key",
            string_value=str(
                backstage_local_asset_bucket_config_inputs.bucket_access_root_key
            ),
            description="Root s3 prefix to give backstage access to in the local asset bucket",
            parameter_name=ResourceName.slash_separated(
                prefix=acdp_config_ssm_prefix,
                name=f"{local_asset_config_ssm_path}/root-s3-key",
            ),
            simple_name=True,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-local-asset-config-asset-bucket-default-assets-prefix",
            string_value=str(
                backstage_local_asset_bucket_config_inputs.backstage_default_assets_prefix
            ),
            description="S3 prefix for default ACDP deployable assets in the local asset bucket",
            parameter_name=ResourceName.slash_separated(
                prefix=acdp_config_ssm_prefix,
                name=f"{local_asset_config_ssm_path}/default-assets-prefix",
            ),
            simple_name=True,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-local-asset-config-asset-bucket-backstage-custom-template-key-prefix",
            string_value=str(
                backstage_local_asset_bucket_config_inputs.backstage_user_provided_template_key_prefix
            ),
            description="Bucket key prefix for the local bucket where custom ACDP deployable resources are discovered",
            parameter_name=ResourceName.slash_separated(
                prefix=acdp_config_ssm_prefix,
                name=f"{local_asset_config_ssm_path}/backstage-custom-template-key-prefix",
            ),
            simple_name=True,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-local-asset-config-asset-bucket-backstage-default-template-key-prefix",
            string_value=str(
                backstage_local_asset_bucket_config_inputs.backstage_default_template_key_prefix
            ),
            description="Bucket key prefix for the local bucket where deafault ACDP deployable resources are discovered",
            parameter_name=ResourceName.slash_separated(
                prefix=acdp_config_ssm_prefix,
                name=f"{local_asset_config_ssm_path}/backstage-default-template-key-prefix",
            ),
            simple_name=True,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-local-asset-config-asset-bucket-catalog-key-prefix",
            string_value=str(
                backstage_local_asset_bucket_config_inputs.catalog_key_prefix
            ),
            description="Bucket key prefix where Backstage Catalog Items are published to",
            parameter_name=ResourceName.slash_separated(
                prefix=acdp_config_ssm_prefix,
                name=f"{local_asset_config_ssm_path}/catalog-key-prefix",
            ),
            simple_name=True,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-local-asset-config-asset-bucket-techdocs-key-prefix",
            string_value=str(
                backstage_local_asset_bucket_config_inputs.techdocs_key_prefix
            ),
            description="Bucket key prefix where Techdocs resources are published to",
            parameter_name=ResourceName.slash_separated(
                prefix=acdp_config_ssm_prefix,
                name=f"{local_asset_config_ssm_path}/techdocs-key-prefix",
            ),
            simple_name=True,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-local-asset-config-backstage-discovery-refresh-freq-mins",
            string_value=str(
                backstage_local_asset_bucket_config_inputs.discovery_refresh_frequency_mins
            ),
            description="Frequency to allow refresh of Backstage catalog provider from the local bucket",
            parameter_name=ResourceName.slash_separated(
                prefix=acdp_config_ssm_prefix,
                name=f"{local_asset_config_ssm_path}/discovery-refresh-frequency-mins",
            ),
            simple_name=True,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-codebuild-project-arn",
            string_value=codebuild_project_arn,
            description="CodeBuild Project ARN for Backstage ACDP plugin",
            parameter_name=ResourceName.slash_separated(
                prefix=acdp_config_ssm_prefix,
                name="codebuild-project/arn",
            ),
            simple_name=True,
        )
