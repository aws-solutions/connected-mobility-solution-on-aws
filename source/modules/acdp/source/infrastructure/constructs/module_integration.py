# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Union

# Third Party Libraries
from attrs import define

# AWS Libraries
from aws_cdk import CfnCondition, CfnMapping, CfnParameter, Fn, Stack, aws_s3, aws_ssm
from constructs import Construct

# CMS Common Library
from cms_common.config.regex import RegexPattern
from cms_common.config.resource_names import ResourceName, ResourcePrefix
from cms_common.constructs.encrypted_s3 import EncryptedS3Construct, LifecycleConfig
from cms_common.constructs.identity_provider_config import IdentityProviderConfig
from cms_common.constructs.vpc_construct import create_vpc_config
from cms_common.resource_names.module_short_names import CMSModuleShortNames

MINUTES_IN_A_DAY = 1440


@define(auto_attribs=True, frozen=True)
class BackstageS3RegionalAssetsConfigInputs:
    bucket_name: str
    bucket_region: str
    backstage_pipeline_zip_asset_key: str
    backstage_template_key_prefix: str
    buildspec_key_prefix: str
    discovery_refresh_frequency_mins: Union[int, float]


@define(auto_attribs=True, frozen=True)
class BackstageS3LocalAssetsConfigInputs:
    bucket: aws_s3.IBucket
    bucket_name: str
    bucket_region: str
    entities_prefix: str
    default_assets_prefix: str
    default_entities_prefix: str
    catalog_key_prefix: str
    techdocs_key_prefix: str
    discovery_refresh_frequency_mins: Union[int, float]


@define(auto_attribs=True, frozen=True)
class BackstageDomainInputParameters:
    route53_hosted_zone_id_parameter: aws_ssm.IStringParameter
    fully_qualified_domain_name_parameter: aws_ssm.IStringParameter
    custom_acm_certificate_arn_parameter: aws_ssm.IStringParameter
    is_public_facing_parameter: aws_ssm.IStringParameter


@define(auto_attribs=True, frozen=True)
class BackstageGeneralConfigInputs:
    name: str
    org: str
    log_level: str


@define(auto_attribs=True, frozen=True)
class BackstageAuthConfigInputs:
    identity_provider_id: str
    use_auth_redirect_flow: str
    additional_scopes: str
    should_create_cognito_user: str
    admin_user_email: str
    admin_username: str


@define(auto_attribs=True, frozen=True)
class BackstageMultiAcctSetupInputs:
    enable_multi_account_deployment: str
    orgs_management_aws_account_id: str
    orgs_management_account_region: str


class ModuleInputsConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        solution_mapping: CfnMapping,
        local_asset_bucket_construct: EncryptedS3Construct,
        backstage_s3_assets_key_prefix: str,
        log_lifecycle_rules: LifecycleConfig,
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

        self.log_lifecycle_rules = log_lifecycle_rules

        self.acdp_config_ssm_prefix = ResourcePrefix.slash_separated(
            app_unique_id=self.acdp_uid,
            module_name=CMSModuleShortNames.CONFIG,
            leading_slash=True,
        )

        self.acdp_multi_acct_ssm_prefix = ResourcePrefix.slash_separated(
            app_unique_id=self.acdp_uid,
            module_name="multi-acct",
            leading_slash=True,
        )

        # Backstage Domain Inputs
        # Rather than creating SSM parameters in ModuleOutputsConstruct similar to other config,
        # these SSM Parameters are created immediately so they can be used in the Pipelines construct, specifically the backstage pipeline environment
        is_public_facing = CfnParameter(
            Stack.of(self),
            "IsPublicFacing",
            type="String",
            description="Boolean flag that configures if public endpoints should be created for ACDP/Backstage resources. If true, the VPC must have an Internet Gateway",
            allowed_values=["true", "false"],
            constraint_description=("Value must be boolean (true, false)"),
            default="true",
        ).value_as_string

        fully_qualified_domain_name = CfnParameter(
            Stack.of(self),
            "FullyQualifiedDomainName",
            type="String",
            description="Fully Qualified Domain Name for ACDP resources to be accessed. If using Route53, this must be a subset of the Route53 Zone Name",
            allowed_pattern=RegexPattern.DOMAIN_NAME,
            constraint_description="Fully Qualified Domain Name must be a valid domain name",
        ).value_as_string

        route53_hosted_zone_id = CfnParameter(
            Stack.of(self),
            "Route53HostedZoneId",
            type="String",
            description="Optional: Id of the Route53 Hosted Zone. Set to create records in Route53 for the required DNS entries.",
            default="",
            allowed_pattern="^(|Z[A-Z0-9]{1,30})$",
            constraint_description="Must be '' or a valid Route53 Hosted Zone Id",
        ).value_as_string

        custom_acm_certificate_arn = CfnParameter(
            Stack.of(self),
            "CustomAcmCertificateArn",
            type="String",
            description=(
                "Optional when using a Public Hosted Zone with Route53. "
                "Required when HostedZoneId is Private or not provided. "
                "Provide a custom ACM Certificate ARN to use for TLS."
            ),
            default="",
            allowed_pattern=r"(^$)|(^arn:aws:acm:[a-z0-9-]+:\d{12}:certificate/[a-f0-9-]+$)",
            constraint_description="Must be '' or a valid ACM certificate ARN",
        ).value_as_string

        is_route53_hosted_zone_id_set = CfnCondition(
            self,
            "is-route53-hosted-zone-id-set-condition",
            expression=Fn.condition_not(
                Fn.condition_equals(lhs=route53_hosted_zone_id, rhs="")
            ),
        )

        is_custom_acm_certificate_arn_set = CfnCondition(
            self,
            "is-custom-acm-certificate-arn-set-condition",
            expression=Fn.condition_not(
                Fn.condition_equals(lhs=custom_acm_certificate_arn, rhs="")
            ),
        )

        self.backstage_domain_input_parameters = BackstageDomainInputParameters(  # SSM Parameters used in pipeline environment
            route53_hosted_zone_id_parameter=aws_ssm.StringParameter(
                self,
                "ssm-route53-hosted-zone-name",
                string_value=Fn.condition_if(
                    is_route53_hosted_zone_id_set.logical_id,
                    route53_hosted_zone_id,
                    "unset",
                ).to_string(),
                description="The id of the Route53 hosted zone to deploy in if Route53 is used",
                parameter_name=ResourceName.slash_separated(
                    prefix=self.acdp_config_ssm_prefix,
                    name="dns/route53-hosted-zone-id",
                ),
                simple_name=False,
            ),
            custom_acm_certificate_arn_parameter=aws_ssm.StringParameter(
                self,
                "ssm-acm-custom-certificate-arn",
                string_value=Fn.condition_if(
                    is_custom_acm_certificate_arn_set.logical_id,
                    custom_acm_certificate_arn,
                    "unset",
                ).to_string(),
                description=(
                    "Optional when using a Public Hosted Zone with Route53. "
                    "Required when HostedZoneId is Private or not provided. "
                    "Provide a custom ACM Certificate ARN to use for TLS."
                ),
                parameter_name=ResourceName.slash_separated(
                    prefix=self.acdp_config_ssm_prefix,
                    name="dns/acm-custom-certificate-arn",
                ),
                simple_name=False,
            ),
            is_public_facing_parameter=aws_ssm.StringParameter(
                self,
                "ssm-is-public-facing",
                string_value=is_public_facing,
                description="Boolean value representing if public endpoints should be created for relevant resources",
                parameter_name=ResourceName.slash_separated(
                    prefix=self.acdp_config_ssm_prefix,
                    name="dns/is-public-facing",
                ),
                simple_name=False,
            ),
            fully_qualified_domain_name_parameter=aws_ssm.StringParameter(
                self,
                "ssm-fully-qualified-domain-name",
                string_value=fully_qualified_domain_name,
                description="The name of the base domain to deploy in",
                parameter_name=ResourceName.slash_separated(
                    prefix=self.acdp_config_ssm_prefix,
                    name="dns/fully-qualified-domain-name",
                ),
                simple_name=False,
            ),
        )

        # Backstage General Config Inputs
        self.backstage_general_config_inputs = BackstageGeneralConfigInputs(
            name=CfnParameter(
                Stack.of(self),
                "BackstageName",
                type="String",
                description="Name to use for the Backstage Portal",
                default="ACDP",
                allowed_pattern=RegexPattern.GENERIC_NAME,
                constraint_description="Backstage Name must begin and end with an alphanumeric character and only consist of alphanumeric characters, space, hyphen(-) and underscore(_)",
            ).value_as_string,
            org=CfnParameter(
                Stack.of(self),
                "BackstageOrg",
                type="String",
                description="Organization Name to use for the Backstage Portal",
                default="Auto",
                allowed_pattern=RegexPattern.GENERIC_NAME,
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

        # Backstage Auth Config Inputs
        backstage_additional_scopes = CfnParameter(
            Stack.of(self),
            "BackstageAdditionalScopes",
            type="String",
            description="Additional scopes which Backstage will request from the configured identity provider on sign-in",
            default="",
            allowed_pattern=RegexPattern.SCOPES,
            constraint_description="Scopes should be a space separated list of strings, allowing most printable ASCII characters",
        ).value_as_string

        is_backstage_additional_scopes_set = CfnCondition(
            self,
            "is-backstage-additional-scopes-set-condition",
            expression=Fn.condition_not(
                Fn.condition_equals(lhs=backstage_additional_scopes, rhs="")
            ),
        )

        admin_user_email = CfnParameter(
            Stack.of(self),
            "AdminUserEmail",
            type="String",
            description="The user E-Mail to access backstage UI",
            allowed_pattern=RegexPattern.OPTIONAL_EMAIL,
            constraint_description="User E-Mail must be a valid E-Mail address",
        ).value_as_string

        admin_username = Fn.select(0, Fn.split("@", admin_user_email))

        self.backstage_auth_config_inputs = BackstageAuthConfigInputs(
            identity_provider_id=IdentityProviderConfig.create_cfn_parameter(
                Stack.of(self)
            ),
            use_auth_redirect_flow=CfnParameter(
                Stack.of(self),
                "UseBackstageAuthRedirectFlow",
                type="String",
                description="Boolean flag that determines whether Backstage uses an experimental redirect flow instead of the default popup flow",
                allowed_values=["true", "false"],
                constraint_description=("Value must be boolean (true, false)"),
                default="true",
            ).value_as_string,
            additional_scopes=Fn.condition_if(
                is_backstage_additional_scopes_set.logical_id,
                backstage_additional_scopes,
                "cms-unset",
            ).to_string(),
            should_create_cognito_user=CfnParameter(
                Stack.of(self),
                "ShouldCreateCognitoUser",
                type="String",
                description="Boolean flag that determined whether to create an Amazon Cognito user using the Admin user email.",
                allowed_values=["true", "false"],
                constraint_description=("Value must be boolean (true, false)"),
                default="true",
            ).value_as_string,
            admin_user_email=admin_user_email,
            admin_username=admin_username,
        )

        # Backstage S3 Regional Assets Inputs
        self.regional_asset_bucket_inputs = BackstageS3RegionalAssetsConfigInputs(
            bucket_name=f'{solution_mapping.find_in_map("AssetsConfig", "S3AssetBucketBaseName")}-{Stack.of(self).region}',
            bucket_region=Stack.of(self).region,
            backstage_pipeline_zip_asset_key=f"{backstage_s3_assets_key_prefix}/pipeline/backstage_pipeline_source.zip",
            backstage_template_key_prefix=f"{backstage_s3_assets_key_prefix}/templates",
            buildspec_key_prefix=f"{backstage_s3_assets_key_prefix}/acdp",
            discovery_refresh_frequency_mins=MINUTES_IN_A_DAY,
        )

        # Backstage S3 Local Assets Inputs
        backstage_local_asset_bucket_entities_prefix = "backstage"
        backstage_local_asset_bucket_default_assets_prefix = "backstage-default-assets"
        self.local_asset_bucket_inputs = BackstageS3LocalAssetsConfigInputs(
            bucket=local_asset_bucket_construct.bucket,
            bucket_name=local_asset_bucket_construct.bucket.bucket_name,
            bucket_region=Stack.of(self).region,
            entities_prefix=backstage_local_asset_bucket_entities_prefix,
            default_assets_prefix=backstage_local_asset_bucket_default_assets_prefix,
            default_entities_prefix=f"{backstage_local_asset_bucket_default_assets_prefix}/entities",
            catalog_key_prefix=f"{backstage_local_asset_bucket_entities_prefix}/catalog",
            techdocs_key_prefix=f"{backstage_local_asset_bucket_entities_prefix}/techdocs",
            discovery_refresh_frequency_mins=CfnParameter(
                Stack.of(self),
                "BackstageLocalAssetDiscoveryRefreshMins",
                type="Number",
                description="Refresh Frequency (minutes) for Backstage catalog provider from the Backstage Local Asset Bucket",
                min_value=1,
                default=30,
            ).value_as_number,
        )

        self.backstage_multi_acct_setup_inputs = BackstageMultiAcctSetupInputs(
            enable_multi_account_deployment=CfnParameter(
                Stack.of(self),
                "EnableMultiAccountDeployment",
                type="String",
                description="Boolean flag that configures multi account deployment support",
                allowed_values=["true", "false"],
                constraint_description=("Value must be boolean (true, false)"),
                default="false",
            ).value_as_string,
            orgs_management_aws_account_id=CfnParameter(
                Stack.of(self),
                "OrgsManagementAwsAccountId",
                description="The 12-digit AWS account ID where Org Management Account resources are deployed. This is only required if EnableMultiAccountDeployment is set to true.",
                type="String",
                allowed_pattern=r"^\d{12}$|null$",
                constraint_description="AWS Account Id must be a 12-digit number. This is only required if EnableMultiAccountDeployment is set to true.",
                default="null",
            ).value_as_string,
            orgs_management_account_region=CfnParameter(
                Stack.of(self),
                "OrgsManagementAccountRegion",
                description="Region where org management accounts resources are located",
                type="String",
                allowed_pattern=r"^(us|eu|ap|sa|ca|me|af|il)-(north|south|east|west|central)-(1|2|3|4)$|null$",
                constraint_description="Provide valid region name[Non government regions only]",
                default="null",
            ).value_as_string,
        )


class ModuleOutputsConstruct(Construct):  # pylint: disable=too-many-arguments
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        deployment_uuid: str,
        acdp_config_ssm_prefix: str,
        backstage_ecr_name: str,
        backstage_pipeline_name: str,
        codebuild_project_arn: str,
        backstage_auth_config_inputs: BackstageAuthConfigInputs,
        backstage_general_config_inputs: BackstageGeneralConfigInputs,
        backstage_regional_asset_config_inputs: BackstageS3RegionalAssetsConfigInputs,
        backstage_local_asset_bucket_config_inputs: BackstageS3LocalAssetsConfigInputs,
        acdp_multi_acct_ssm_prefix: str,
        backstage_multi_acct_setup_inputs: BackstageMultiAcctSetupInputs,
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
            simple_name=False,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-backstage-ecr-repository-name",
            string_value=backstage_ecr_name,
            description="Backstage ECR Repository Name",
            parameter_name=ResourceName.slash_separated(
                prefix=acdp_config_ssm_prefix,
                name="backstage/ecr-repository/name",
            ),
            simple_name=False,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-codepipeline-project-name",
            string_value=backstage_pipeline_name,
            description="CodePipeline Project Name for ACDP Backstage Deployment",
            parameter_name=ResourceName.slash_separated(
                prefix=acdp_config_ssm_prefix,
                name="codepipeline-project/name",
            ),
            simple_name=False,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-codebuild-project-arn-multi",
            string_value=codebuild_project_arn,
            description="CodeBuild Project ARN for Backstage ACDP plugin (Multi-Account)",
            parameter_name=ResourceName.slash_separated(
                prefix=acdp_config_ssm_prefix,
                name="codebuild-project/arn",
            ),
            simple_name=False,
        )

        # Backstage Auth Config
        aws_ssm.StringParameter(
            self,
            "ssm-backstage-use-auth-redirect-flow",
            string_value=backstage_auth_config_inputs.use_auth_redirect_flow,
            description="Whether Backstage should use the experimental auth redirect flow rather than the default popup flow",
            parameter_name=ResourceName.slash_separated(
                prefix=acdp_config_ssm_prefix, name="backstage/use-auth-redirect-flow"
            ),
            simple_name=False,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-backstage-additional-scopes",
            string_value=backstage_auth_config_inputs.additional_scopes,
            description="Additional scopes which Backstage will request from the configured identity provider on login",
            parameter_name=ResourceName.slash_separated(
                prefix=acdp_config_ssm_prefix, name="backstage/additional-scopes"
            ),
            simple_name=False,
        )

        # Backstage General Config
        aws_ssm.StringParameter(
            self,
            "ssm-backstage-name",
            string_value=backstage_general_config_inputs.name,
            description="The name to display on Backstage",
            parameter_name=ResourceName.slash_separated(
                prefix=acdp_config_ssm_prefix, name="backstage/name"
            ),
            simple_name=False,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-backstage-org",
            string_value=backstage_general_config_inputs.org,
            description="The organization to display on Backstage",
            parameter_name=ResourceName.slash_separated(
                prefix=acdp_config_ssm_prefix,
                name="backstage/organization",
            ),
            simple_name=False,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-backstage-log-level",
            string_value=backstage_general_config_inputs.log_level,
            description="Level of logs to display (trace, debug, info, warn, error, critical)",
            parameter_name=ResourceName.slash_separated(
                prefix=acdp_config_ssm_prefix, name="backstage/log-level"
            ),
            simple_name=False,
        )

        # Backstage Regional Asset Config
        aws_ssm.StringParameter(
            self,
            "ssm-regional-asset-config-bucket-name",
            string_value=backstage_regional_asset_config_inputs.bucket_name,
            description="Name of the regional asset bucket where ACDP Deployable resources are discovered",
            parameter_name=ResourceName.slash_separated(
                prefix=acdp_config_ssm_prefix,
                name=f"{regional_asset_config_ssm_path}/asset-bucket/name",
            ),
            simple_name=False,
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
            simple_name=False,
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
            simple_name=False,
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
            simple_name=False,
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
            simple_name=False,
        )

        # Backstage Local Config
        aws_ssm.StringParameter(
            self,
            "ssm-local-asset-bucket-config-name",
            string_value=backstage_local_asset_bucket_config_inputs.bucket_name,
            description="Name of the local asset bucket where ACDP Deployable resources are discovered",
            parameter_name=ResourceName.slash_separated(
                prefix=acdp_config_ssm_prefix,
                name=f"{local_asset_config_ssm_path}/asset-bucket/name",
            ),
            simple_name=False,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-local-asset-bucket-config-region",
            string_value=backstage_local_asset_bucket_config_inputs.bucket_region,
            description="Region of the local bucket where ACDP Deployable resources are discovered",
            parameter_name=ResourceName.slash_separated(
                prefix=acdp_config_ssm_prefix,
                name=f"{local_asset_config_ssm_path}/asset-bucket/region",
            ),
            simple_name=False,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-local-asset-bucket-config-entitites-prefix",
            string_value=str(
                backstage_local_asset_bucket_config_inputs.entities_prefix
            ),
            description="Root s3 prefix to give backstage access to in the local asset bucket",
            parameter_name=ResourceName.slash_separated(
                prefix=acdp_config_ssm_prefix,
                name=f"{local_asset_config_ssm_path}/entities-prefix",
            ),
            simple_name=False,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-local-asset-bucket-config-default-assets-prefix",
            string_value=str(
                backstage_local_asset_bucket_config_inputs.default_assets_prefix
            ),
            description="S3 prefix for default ACDP assets (docs, buildspecs, entities, etc.) in the local asset bucket",
            parameter_name=ResourceName.slash_separated(
                prefix=acdp_config_ssm_prefix,
                name=f"{local_asset_config_ssm_path}/default-assets-prefix",
            ),
            simple_name=False,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-local-asset-bucket-config-default-entities-prefix",
            string_value=str(
                backstage_local_asset_bucket_config_inputs.default_entities_prefix
            ),
            description="S3 prefix for default ACDP catalog entities (templates, users, groups, etc.) in the local asset bucket",
            parameter_name=ResourceName.slash_separated(
                prefix=acdp_config_ssm_prefix,
                name=f"{local_asset_config_ssm_path}/default-entities-prefix",
            ),
            simple_name=False,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-local-asset-bucket-config-catalog-key-prefix",
            string_value=str(
                backstage_local_asset_bucket_config_inputs.catalog_key_prefix
            ),
            description="Bucket key prefix where Backstage Catalog Items are published to",
            parameter_name=ResourceName.slash_separated(
                prefix=acdp_config_ssm_prefix,
                name=f"{local_asset_config_ssm_path}/catalog-key-prefix",
            ),
            simple_name=False,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-local-asset-bucket-config-techdocs-key-prefix",
            string_value=str(
                backstage_local_asset_bucket_config_inputs.techdocs_key_prefix
            ),
            description="Bucket key prefix where Techdocs resources are published to",
            parameter_name=ResourceName.slash_separated(
                prefix=acdp_config_ssm_prefix,
                name=f"{local_asset_config_ssm_path}/techdocs-key-prefix",
            ),
            simple_name=False,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-local-asset-bucket-config-discovery-refresh-freq-mins",
            string_value=str(
                backstage_local_asset_bucket_config_inputs.discovery_refresh_frequency_mins
            ),
            description="Frequency to allow refresh of Backstage catalog provider from the local bucket",
            parameter_name=ResourceName.slash_separated(
                prefix=acdp_config_ssm_prefix,
                name=f"{local_asset_config_ssm_path}/discovery-refresh-frequency-mins",
            ),
            simple_name=False,
        )

        # Backstage Multi Account Setup Inputs
        aws_ssm.StringParameter(
            self,
            "ssm-multi-acct-orgs-enable-multi-account-deployment",
            string_value=backstage_multi_acct_setup_inputs.enable_multi_account_deployment,
            description="The flag that toggles multi-account-deployment feature",
            parameter_name=ResourceName.slash_separated(
                prefix=acdp_multi_acct_ssm_prefix,
                name="enable-multi-account-deployment",
            ),
            simple_name=False,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-multi-acct-orgs-management-aws-account-id",
            string_value=backstage_multi_acct_setup_inputs.orgs_management_aws_account_id,
            description="The 12-digit AWS account ID where Org Management Account resources are deployed",
            parameter_name=ResourceName.slash_separated(
                prefix=acdp_multi_acct_ssm_prefix,
                name="orgs-management-account-id",
            ),
            simple_name=False,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-multi-acct-orgs-management-account-aws-region",
            string_value=backstage_multi_acct_setup_inputs.orgs_management_account_region,
            description="Region where org management accounts resources are located",
            parameter_name=ResourceName.slash_separated(
                prefix=acdp_multi_acct_ssm_prefix,
                name="orgs-management-account-region",
            ),
            simple_name=False,
        )
