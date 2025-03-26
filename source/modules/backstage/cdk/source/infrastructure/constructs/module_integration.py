# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from dataclasses import dataclass

# AWS Libraries
from aws_cdk import (
    CfnCondition,
    CfnMapping,
    CfnParameter,
    Fn,
    Stack,
    Token,
    aws_secretsmanager,
    aws_ssm,
)
from constructs import Construct

# CMS Common Library
from cms_common.config.regex import RegexPattern
from cms_common.config.resource_names import ResourceName, ResourcePrefix
from cms_common.config.stack_inputs import SolutionConfigInputs
from cms_common.constructs.encrypted_s3 import EncryptedS3Construct
from cms_common.constructs.identity_provider_config import IdentityProviderConfig
from cms_common.constructs.vpc_construct import create_vpc_config
from cms_common.resource_names.auth import AuthSetupResourceNames


@dataclass(frozen=True)
class AuthConfigurationProperties:
    idp_config: aws_secretsmanager.ISecret
    user_client_config: aws_secretsmanager.ISecret


@dataclass(frozen=True)
class BackstageConfigurationProperties:
    ecr_repository_name: str
    node_env: str
    log_level: str
    user_agent_string: str
    default_target_account_id: aws_ssm.IStringParameter
    default_target_region: aws_ssm.IStringParameter


@dataclass(frozen=True)
class AcdpAssetProperties:
    regional_asset_bucket_name: str
    local_asset_bucket_name: str
    local_asset_bucket_entities_prefix: str
    local_asset_bucket_default_assets_prefix: str
    local_asset_bucket_default_entities_prefix: str


@dataclass(frozen=True)
class DnsProperties:
    fully_qualified_domain_name: str
    route53_hosted_zone_id: str
    custom_acm_certificate_arn: str
    is_public_facing: str
    should_create_route53_records_condition: CfnCondition
    use_acm_dns_certificate_condition: CfnCondition
    use_custom_acm_certificate_condition: CfnCondition


@dataclass(frozen=True)
class BackstageTaskDefinitionSecrets:  # pylint: disable=too-many-instance-attributes
    backstage_name: aws_ssm.IStringParameter
    backstage_org: aws_ssm.IStringParameter
    backstage_use_auth_redirect_flow: aws_ssm.IStringParameter
    backstage_additional_scopes: aws_ssm.IStringParameter
    regional_asset_bucket_name: aws_ssm.IStringParameter
    regional_asset_bucket_region: aws_ssm.IStringParameter
    regional_asset_bucket_template_key_prefix: aws_ssm.IStringParameter
    regional_asset_bucket_buildspec_key_prefix: aws_ssm.IStringParameter
    regional_asset_bucket_discovery_refresh_frequency: aws_ssm.IStringParameter
    local_asset_bucket_name: aws_ssm.IStringParameter
    local_asset_bucket_region: aws_ssm.IStringParameter
    local_asset_bucket_entities_prefix_parameter: aws_ssm.IStringParameter
    local_asset_bucket_default_entities_prefix_parameter: aws_ssm.IStringParameter
    local_asset_bucket_catalog_key_prefix: aws_ssm.IStringParameter
    local_asset_bucket_techdocs_key_prefix: aws_ssm.IStringParameter
    local_asset_bucket_discovery_refresh_frequency_mins: aws_ssm.IStringParameter
    codebuild_project_arn: aws_ssm.IStringParameter
    acdp_build_config_path_root_parameter: aws_ssm.IStringParameter


@dataclass(frozen=True)
class BackstageAccountDirectorySecrets:
    enable_multi_account_deployment: aws_ssm.IStringParameter
    orgs_management_aws_account_id: aws_ssm.IStringParameter
    orgs_management_account_region: aws_ssm.IStringParameter


class ModuleInputsConstruct(Construct):  # pylint: disable=too-many-instance-attributes
    def __init__(  # pylint: disable=too-many-locals,too-many-statements
        self,
        scope: Construct,
        construct_id: str,
        solution_config_inputs: SolutionConfigInputs,
        solution_mapping: CfnMapping,
    ) -> None:
        super().__init__(scope, construct_id)

        # ACDP Config
        self.acdp_uid = CfnParameter(
            Stack.of(self),
            "AcdpUniqueId",
            description="Name of the ACDP deployment",
            default="acdp",
            type="String",
        ).value_as_string

        self.send_anonymous_metrics = Token.as_string(
            Fn.condition_if(
                CfnCondition(
                    self,
                    "is-send-anonymous-metrics-on",
                    expression=Fn.condition_equals(
                        solution_mapping.find_in_map("Config", "SendAnonymousUsage"),
                        "Yes",
                    ),
                ).logical_id,
                "true",
                "false",
            )
        )

        self.admin_user_email = CfnParameter(
            Stack.of(self),
            "AdminUserEmail",
            type="String",
            description="The user email for the initial admin user.",
            allowed_pattern=RegexPattern.OPTIONAL_EMAIL,
            constraint_description="User E-Mail must be a valid E-Mail address",
        ).value_as_string

        self.enable_multi_account_deployment_cfn_parameter = CfnParameter(
            Stack.of(self),
            "EnableMultiAccountDeployment",
            type="String",
            description="Boolean flag that configures multi account deployment support",
            allowed_values=["true", "false"],
            constraint_description=("Value must be boolean (true, false)"),
        ).value_as_string  # CfnCondition only works with CfnParameter

        # Admin username is used for default Cognito user, and for RBAC default Admin/SuperUser
        self.admin_username = Fn.select(0, Fn.split("@", self.admin_user_email))

        self.should_create_cognito_user = CfnParameter(
            Stack.of(self),
            "ShouldCreateCognitoUser",
            type="String",
            description="Boolean flag that determined whether to create an Amazon Cognito user using the Admin user email.",
            allowed_values=["true", "false"],
            constraint_description=("Value must be boolean (true, false)"),
            default="true",
        ).value_as_string

        self.acdp_config_ssm_prefix_with_slash_prefix = ResourcePrefix.slash_separated(
            app_unique_id=self.acdp_uid, module_name="config", leading_slash=True
        )

        self.acdp_build_ssm_prefix_with_slash_prefix = ResourcePrefix.slash_separated(
            app_unique_id=self.acdp_uid, module_name="acdp-build", leading_slash=True
        )

        self.acdp_multi_acct_ssm_prefix = ResourcePrefix.slash_separated(
            app_unique_id=self.acdp_uid,
            module_name="multi-acct",
            leading_slash=True,
        )

        self.acdp_build_ssm_prefix_without_slash_prefix = (
            ResourcePrefix.slash_separated(
                app_unique_id=self.acdp_uid,
                module_name="acdp-build",
                leading_slash=False,
            )
        )

        self.s3_log_lifecycle_rules = (
            EncryptedS3Construct.create_log_lifecycle_cfn_parameters(self)
        )

        # Auth
        use_auth_redirect_flow_parameter = (
            aws_ssm.StringParameter.from_string_parameter_attributes(
                self,
                "ssm-use-auth-redirect-flow-parameter",
                parameter_name=ResourceName.slash_separated(
                    prefix=self.acdp_config_ssm_prefix_with_slash_prefix,
                    name="backstage/use-auth-redirect-flow",
                ),
                simple_name=False,
                force_dynamic_reference=True,
            )
        )

        additional_scopes_parameter = (
            aws_ssm.StringParameter.from_string_parameter_attributes(
                self,
                "ssm-additional-scopes-parameter",
                parameter_name=ResourceName.slash_separated(
                    prefix=self.acdp_config_ssm_prefix_with_slash_prefix,
                    name="backstage/additional-scopes",
                ),
                simple_name=False,
                force_dynamic_reference=True,
            )
        )

        identity_provider_id = IdentityProviderConfig.create_cfn_parameter(
            Stack.of(self)
        )

        self.auth_setup_resource_names = (
            AuthSetupResourceNames.from_identity_provider_id(identity_provider_id)
        )

        self.user_pool_id = aws_ssm.StringParameter.from_string_parameter_attributes(
            self,
            "deployment-uuid",
            parameter_name=self.auth_setup_resource_names.user_pool_id,
            simple_name=False,
            force_dynamic_reference=True,
        ).string_value

        idp_config_secret_arn = aws_ssm.StringParameter.from_string_parameter_attributes(
            self,
            "ssm-idp-config-secret-arn-parameter",
            parameter_name=self.auth_setup_resource_names.idp_config_secret_arn_ssm_parameter,
            simple_name=False,
            force_dynamic_reference=True,
        )

        user_client_config_secret_arn = aws_ssm.StringParameter.from_string_parameter_attributes(
            self,
            "ssm-user-client-config-secret-arn-parameter",
            parameter_name=self.auth_setup_resource_names.user_client_config_secret_arn_ssm_parameter,
            simple_name=False,
            force_dynamic_reference=True,
        )

        idp_config_secret = aws_secretsmanager.Secret.from_secret_complete_arn(
            self,
            "secrets-manager-idp-config-secret",
            secret_complete_arn=idp_config_secret_arn.string_value,
        )

        user_client_config_secret = aws_secretsmanager.Secret.from_secret_complete_arn(
            self,
            "secrets-manager-user-client-secret",
            secret_complete_arn=user_client_config_secret_arn.string_value,
        )

        # VPC
        self.vpc_name = CfnParameter(
            Stack.of(self),
            "VpcName",
            description="name of the imported vpc",
            type="String",
        ).value_as_string

        self.vpc_config = create_vpc_config(
            vpc_name=self.vpc_name,
        )

        # Networking
        route53_hosted_zone_id = CfnParameter(
            Stack.of(self),
            "Route53HostedZoneId",
            type="String",
            description="Optional: Id of the Route53 Hosted Zone. Set to create records in Route53 for the required DNS entries.",
            default="",
            allowed_pattern="^(|unset|Z[A-Z0-9]{1,30})$",
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
            allowed_pattern=r"(^$)|(^unset$)|(^arn:aws:acm:[a-z0-9-]+:\d{12}:certificate/[a-f0-9-]+$)",
            constraint_description="Must be '' or a valid ACM certificate ARN",
        ).value_as_string

        is_public_facing = CfnParameter(
            Stack.of(self),
            "IsPublicFacing",
            type="String",
            description="Boolean flag that configures if public endpoints should be created for Backstage resources. If true, the VPC must have an Internet Gateway",
            allowed_values=["true", "false"],
            constraint_description=("Value must be boolean (true, false)"),
            default="true",
        ).value_as_string

        self.dns_properties = DnsProperties(
            fully_qualified_domain_name=CfnParameter(
                Stack.of(self),
                "FullyQualifiedDomainName",
                type="String",
                description="Fully Qualified Domain Name for ACDP resources to be accessed. If using Route53, this must be a subset of the Route53 Zone Name",
                allowed_pattern=RegexPattern.DOMAIN_NAME,
                constraint_description="Fully Qualified Domain Name must be a valid domain name",
            ).value_as_string,
            route53_hosted_zone_id=route53_hosted_zone_id,
            custom_acm_certificate_arn=custom_acm_certificate_arn,
            is_public_facing=is_public_facing,
            should_create_route53_records_condition=CfnCondition(
                Stack.of(self),
                "should-create-route53-records-condition",
                expression=Fn.condition_not(
                    Fn.condition_or(
                        Fn.condition_equals(lhs=route53_hosted_zone_id, rhs="unset"),
                        Fn.condition_equals(lhs=route53_hosted_zone_id, rhs=""),
                    )
                ),
            ),
            use_acm_dns_certificate_condition=CfnCondition(
                Stack.of(self),
                "use-acm-dns-certificate-condition",
                expression=Fn.condition_or(
                    Fn.condition_equals(lhs=custom_acm_certificate_arn, rhs="unset"),
                    Fn.condition_equals(lhs=custom_acm_certificate_arn, rhs=""),
                ),
            ),
            use_custom_acm_certificate_condition=CfnCondition(
                Stack.of(self),
                "use-acm-custom-certificate-condition",
                expression=Fn.condition_not(
                    Fn.condition_or(
                        Fn.condition_equals(
                            lhs=custom_acm_certificate_arn, rhs="unset"
                        ),
                        Fn.condition_equals(lhs=custom_acm_certificate_arn, rhs=""),
                    )
                ),
            ),
        )

        # Regional assets
        regional_asset_config_ssm_path = "acdp-asset-config/regional"

        regional_asset_bucket_name_parameter = (
            aws_ssm.StringParameter.from_string_parameter_attributes(
                self,
                "ssm-regional-asset-bucket-name-parameter",
                parameter_name=ResourceName.slash_separated(
                    prefix=self.acdp_config_ssm_prefix_with_slash_prefix,
                    name=f"{regional_asset_config_ssm_path}/asset-bucket/name",
                ),
                simple_name=False,
                force_dynamic_reference=True,
            )
        )

        regional_asset_bucket_region_parameter = (
            aws_ssm.StringParameter.from_string_parameter_attributes(
                self,
                "ssm-regional-asset-bucket-region-parameter",
                parameter_name=ResourceName.slash_separated(
                    prefix=self.acdp_config_ssm_prefix_with_slash_prefix,
                    name=f"{regional_asset_config_ssm_path}/asset-bucket/region",
                ),
                simple_name=False,
                force_dynamic_reference=True,
            )
        )

        regional_asset_bucket_template_key_prefix_parameter = aws_ssm.StringParameter.from_string_parameter_attributes(
            self,
            "ssm-regional-asset-bucket-template-key-prefix-parameter",
            parameter_name=ResourceName.slash_separated(
                prefix=self.acdp_config_ssm_prefix_with_slash_prefix,
                name=f"{regional_asset_config_ssm_path}/backstage-template-key-prefix",
            ),
            simple_name=False,
            force_dynamic_reference=True,
        )

        regional_asset_bucket_buildspec_key_prefix_parameter = (
            aws_ssm.StringParameter.from_string_parameter_attributes(
                self,
                "ssm-regional-asset-bucket-buildspec-key-prefix-parameter",
                parameter_name=ResourceName.slash_separated(
                    prefix=self.acdp_config_ssm_prefix_with_slash_prefix,
                    name=f"{regional_asset_config_ssm_path}/buildspec-key-prefix",
                ),
                simple_name=False,
                force_dynamic_reference=True,
            )
        )

        regional_asset_bucket_discovery_refresh_frequency_mins_parameter = aws_ssm.StringParameter.from_string_parameter_attributes(
            self,
            "ssm-regional-asset-bucket-refresh-frequency-mins-parameter",
            parameter_name=ResourceName.slash_separated(
                prefix=self.acdp_config_ssm_prefix_with_slash_prefix,
                name=f"{regional_asset_config_ssm_path}/discovery-refresh-frequency-mins",
            ),
            simple_name=False,
            force_dynamic_reference=True,
        )

        # Local assets
        local_asset_config_ssm_path = "acdp-asset-config/local"

        local_asset_bucket_name_parameter = (
            aws_ssm.StringParameter.from_string_parameter_attributes(
                self,
                "ssm-local-asset-bucket-config-name",
                parameter_name=ResourceName.slash_separated(
                    prefix=self.acdp_config_ssm_prefix_with_slash_prefix,
                    name=f"{local_asset_config_ssm_path}/asset-bucket/name",
                ),
                simple_name=False,
                force_dynamic_reference=True,
            )
        )

        local_asset_bucket_region_parameter = (
            aws_ssm.StringParameter.from_string_parameter_attributes(
                self,
                "ssm-local-asset-bucket-config-region",
                parameter_name=ResourceName.slash_separated(
                    prefix=self.acdp_config_ssm_prefix_with_slash_prefix,
                    name=f"{local_asset_config_ssm_path}/asset-bucket/region",
                ),
                simple_name=False,
                force_dynamic_reference=True,
            )
        )

        local_asset_bucket_entities_prefix_parameter = (
            aws_ssm.StringParameter.from_string_parameter_attributes(
                self,
                "ssm-local-asset-bucket-config-entities-prefix",
                parameter_name=ResourceName.slash_separated(
                    prefix=self.acdp_config_ssm_prefix_with_slash_prefix,
                    name=f"{local_asset_config_ssm_path}/entities-prefix",
                ),
                simple_name=False,
                force_dynamic_reference=True,
            )
        )

        local_asset_bucket_default_assets_prefix_parameter = (
            aws_ssm.StringParameter.from_string_parameter_attributes(
                self,
                "ssm-local-asset-bucket-config-default-assets-prefix",
                parameter_name=ResourceName.slash_separated(
                    prefix=self.acdp_config_ssm_prefix_with_slash_prefix,
                    name=f"{local_asset_config_ssm_path}/default-assets-prefix",
                ),
                simple_name=False,
                force_dynamic_reference=True,
            )
        )

        local_asset_bucket_default_entities_prefix_parameter = (
            aws_ssm.StringParameter.from_string_parameter_attributes(
                self,
                "ssm-local-asset-bucket-config-default-entities-prefix",
                parameter_name=ResourceName.slash_separated(
                    prefix=self.acdp_config_ssm_prefix_with_slash_prefix,
                    name=f"{local_asset_config_ssm_path}/default-entities-prefix",
                ),
                simple_name=False,
                force_dynamic_reference=True,
            )
        )

        local_asset_bucket_catalog_key_prefix_parameter = (
            aws_ssm.StringParameter.from_string_parameter_attributes(
                self,
                "ssm-local-asset-bucket-config-asset-bucket-catalog-key-prefix",
                parameter_name=ResourceName.slash_separated(
                    prefix=self.acdp_config_ssm_prefix_with_slash_prefix,
                    name=f"{local_asset_config_ssm_path}/catalog-key-prefix",
                ),
                simple_name=False,
                force_dynamic_reference=True,
            )
        )

        local_asset_bucket_techdocs_key_prefix_parameter = (
            aws_ssm.StringParameter.from_string_parameter_attributes(
                self,
                "ssm-local-asset-bucket-config-techdocs-key-prefix",
                parameter_name=ResourceName.slash_separated(
                    prefix=self.acdp_config_ssm_prefix_with_slash_prefix,
                    name=f"{local_asset_config_ssm_path}/techdocs-key-prefix",
                ),
                simple_name=False,
                force_dynamic_reference=True,
            )
        )

        local_asset_bucket_discovery_refresh_frequency_mins_parameter = aws_ssm.StringParameter.from_string_parameter_attributes(
            self,
            "ssm-local-asset-bucket-config-discovery-refresh-freq-mins",
            parameter_name=ResourceName.slash_separated(
                prefix=self.acdp_config_ssm_prefix_with_slash_prefix,
                name=f"{local_asset_config_ssm_path}/discovery-refresh-frequency-mins",
            ),
            simple_name=False,
            force_dynamic_reference=True,
        )

        # Backstage
        codebuild_project_arn_parameter = (
            aws_ssm.StringParameter.from_string_parameter_attributes(
                self,
                "ssm-codebuild-project-arn-parameter",
                parameter_name=ResourceName.slash_separated(
                    prefix=self.acdp_config_ssm_prefix_with_slash_prefix,
                    name="codebuild-project/arn",
                ),
                simple_name=False,
                force_dynamic_reference=True,
            )
        )

        backstage_name_parameter = (
            aws_ssm.StringParameter.from_string_parameter_attributes(
                self,
                "ssm-backstage-name-parameter",
                parameter_name=ResourceName.slash_separated(
                    prefix=self.acdp_config_ssm_prefix_with_slash_prefix,
                    name="backstage/name",
                ),
                simple_name=False,
                force_dynamic_reference=True,
            )
        )

        backstage_org_parameter = (
            aws_ssm.StringParameter.from_string_parameter_attributes(
                self,
                "ssm-backstage-org-parameter",
                parameter_name=ResourceName.slash_separated(
                    prefix=self.acdp_config_ssm_prefix_with_slash_prefix,
                    name="backstage/organization",
                ),
                simple_name=False,
                force_dynamic_reference=True,
            )
        )

        backstage_ecr_repository_name_parameter = (
            aws_ssm.StringParameter.from_string_parameter_attributes(
                self,
                "ssm-backstage-ecr-repository-name",
                parameter_name=ResourceName.slash_separated(
                    prefix=self.acdp_config_ssm_prefix_with_slash_prefix,
                    name="backstage/ecr-repository/name",
                ),
                simple_name=False,
                force_dynamic_reference=True,
            )
        )

        backstage_log_level_parameter = (
            aws_ssm.StringParameter.from_string_parameter_attributes(
                self,
                "ssm-backstage-log-level",
                parameter_name=ResourceName.slash_separated(
                    prefix=self.acdp_config_ssm_prefix_with_slash_prefix,
                    name="backstage/log-level",
                ),
                simple_name=False,
                force_dynamic_reference=True,
            )
        )

        acdp_build_config_path_root_parameter = aws_ssm.StringParameter(
            self,
            "ssm-acdp-build-config-ssm-prefix",
            string_value=self.acdp_build_ssm_prefix_with_slash_prefix,
            description="Description for acdp build config path root parameter",
            parameter_name=ResourceName.slash_separated(
                prefix=self.acdp_build_ssm_prefix_with_slash_prefix,
                name="build-config-ssm-prefix",
            ),
            simple_name=False,
        )

        default_target_account_id = aws_ssm.StringParameter(
            self,
            "ssm-backstage-default-target-account-id",
            string_value=Stack.of(self).account,
            description="Backstage Deployment Target Account Id",
            parameter_name=ResourceName.slash_separated(
                prefix=self.acdp_config_ssm_prefix_with_slash_prefix,
                name="deployment-targets/default/account-id",
            ),
            simple_name=False,
        )

        default_target_region = aws_ssm.StringParameter(
            self,
            "ssm-backstage-default-target-region",
            string_value=Stack.of(self).region,
            description="Backstage Deployment Target Region",
            parameter_name=ResourceName.slash_separated(
                prefix=self.acdp_config_ssm_prefix_with_slash_prefix,
                name="deployment-targets/default/region",
            ),
            simple_name=False,
        )

        # Backstage Account Directory Inputs
        enable_multi_account_deployment = (
            aws_ssm.StringParameter.from_string_parameter_attributes(
                self,
                "ssm-multi-acct-orgs-enable-multi-account-deployment",
                parameter_name=ResourceName.slash_separated(
                    prefix=self.acdp_multi_acct_ssm_prefix,
                    name="enable-multi-account-deployment",
                ),
                simple_name=False,
                force_dynamic_reference=True,
            )
        )

        org_management_aws_account_id = (
            aws_ssm.StringParameter.from_string_parameter_attributes(
                self,
                "ssm-orgs-account-id",
                parameter_name=ResourceName.slash_separated(
                    prefix=self.acdp_multi_acct_ssm_prefix,
                    name="orgs-management-account-id",
                ),
                simple_name=False,
                force_dynamic_reference=True,
            )
        )

        orgs_management_account_region = (
            aws_ssm.StringParameter.from_string_parameter_attributes(
                self,
                "ssm-orgs-account-region",
                parameter_name=ResourceName.slash_separated(
                    prefix=self.acdp_multi_acct_ssm_prefix,
                    name="orgs-management-account-region",
                ),
                simple_name=False,
                force_dynamic_reference=True,
            )
        )

        # Property consolidation
        self.auth_configuration_properties = AuthConfigurationProperties(
            idp_config=idp_config_secret,
            user_client_config=user_client_config_secret,
        )

        self.acdp_asset_properties = AcdpAssetProperties(
            regional_asset_bucket_name=regional_asset_bucket_name_parameter.string_value,
            local_asset_bucket_name=local_asset_bucket_name_parameter.string_value,
            local_asset_bucket_entities_prefix=local_asset_bucket_entities_prefix_parameter.string_value,
            local_asset_bucket_default_assets_prefix=local_asset_bucket_default_assets_prefix_parameter.string_value,
            local_asset_bucket_default_entities_prefix=local_asset_bucket_default_entities_prefix_parameter.string_value,
        )

        self.backstage_configuration = BackstageConfigurationProperties(
            ecr_repository_name=backstage_ecr_repository_name_parameter.string_value,
            node_env="production",
            log_level=backstage_log_level_parameter.string_value,
            user_agent_string=solution_config_inputs.get_user_agent_string(),
            default_target_account_id=default_target_account_id,
            default_target_region=default_target_region,
        )

        self.backstage_task_definition_secrets = BackstageTaskDefinitionSecrets(
            backstage_name=backstage_name_parameter,
            backstage_org=backstage_org_parameter,
            backstage_use_auth_redirect_flow=use_auth_redirect_flow_parameter,
            backstage_additional_scopes=additional_scopes_parameter,
            regional_asset_bucket_name=regional_asset_bucket_name_parameter,
            regional_asset_bucket_region=regional_asset_bucket_region_parameter,
            regional_asset_bucket_template_key_prefix=regional_asset_bucket_template_key_prefix_parameter,
            regional_asset_bucket_buildspec_key_prefix=regional_asset_bucket_buildspec_key_prefix_parameter,
            regional_asset_bucket_discovery_refresh_frequency=regional_asset_bucket_discovery_refresh_frequency_mins_parameter,
            local_asset_bucket_name=local_asset_bucket_name_parameter,
            local_asset_bucket_region=local_asset_bucket_region_parameter,
            local_asset_bucket_entities_prefix_parameter=local_asset_bucket_entities_prefix_parameter,
            local_asset_bucket_default_entities_prefix_parameter=local_asset_bucket_default_entities_prefix_parameter,
            local_asset_bucket_catalog_key_prefix=local_asset_bucket_catalog_key_prefix_parameter,
            local_asset_bucket_techdocs_key_prefix=local_asset_bucket_techdocs_key_prefix_parameter,
            local_asset_bucket_discovery_refresh_frequency_mins=local_asset_bucket_discovery_refresh_frequency_mins_parameter,
            codebuild_project_arn=codebuild_project_arn_parameter,
            acdp_build_config_path_root_parameter=acdp_build_config_path_root_parameter,
        )

        self.backstage_account_directory_secrets = BackstageAccountDirectorySecrets(
            enable_multi_account_deployment=enable_multi_account_deployment,
            orgs_management_aws_account_id=org_management_aws_account_id,
            orgs_management_account_region=orgs_management_account_region,
        )
