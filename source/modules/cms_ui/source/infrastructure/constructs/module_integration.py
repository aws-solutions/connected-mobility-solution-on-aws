# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library

# Third Party Libraries
from attrs import define

# AWS Libraries
from aws_cdk import CfnOutput, CfnParameter, Stack, aws_ssm
from constructs import Construct

# CMS Common Library
from cms_common.config.metrics import OperationalMetricsInput
from cms_common.config.resource_names import ResourceName, ResourcePrefix
from cms_common.config.ssm import resolve_ssm_parameter
from cms_common.config.stack_inputs import SolutionConfigInputs
from cms_common.constructs.app_unique_id import AppUniqueId
from cms_common.constructs.encrypted_s3 import EncryptedS3Construct
from cms_common.constructs.identity_provider_config import IdentityProviderConfig
from cms_common.constructs.vpc_construct import create_vpc_config, get_vpc_name
from cms_common.resource_names.auth import AuthResourceNames, AuthSetupResourceNames
from cms_common.resource_names.config import ConfigResourceNames


@define(auto_attribs=True, frozen=True)
class ModuleConfigInputs:
    app_unique_id: str
    module_ssm_prefix: str


@define(frozen=True)
class TokenValidationInputs:
    lambda_arn: str


@define(frozen=True)
class CognitoConfigInputs:
    cognito_user_pool_id: str
    idp_config_secret_arn: str


class ModuleInputsConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        solution_config_inputs: SolutionConfigInputs,
    ) -> None:
        super().__init__(scope, construct_id)

        self.app_unique_id = AppUniqueId.create_cfn_parameter(Stack.of(self))

        self.identity_provider_id = IdentityProviderConfig.get_identity_provider_id(
            scope=self, app_unique_id=self.app_unique_id
        )

        self.vpc_config = create_vpc_config(
            vpc_name=get_vpc_name(self, app_unique_id=self.app_unique_id)
        )

        module_ssm_prefix = ResourcePrefix.slash_separated(
            app_unique_id=self.app_unique_id,
            module_name=solution_config_inputs.module_short_name,
        )

        self.module_config_inputs = ModuleConfigInputs(
            app_unique_id=self.app_unique_id,
            module_ssm_prefix=module_ssm_prefix,
        )

        self.operational_metrics = OperationalMetricsInput.from_app_unique_id(
            app_unique_id=self.app_unique_id
        )

        self.token_validation = TokenValidationInputs(
            lambda_arn=resolve_ssm_parameter(
                parameter_name=AuthResourceNames.from_app_unique_id(
                    app_unique_id=self.app_unique_id
                ).token_validation_lambda_arn,
            ),
        )

        self.auth_setup_resource_names = (
            AuthSetupResourceNames.from_identity_provider_id(self.identity_provider_id)
        )

        self.cms_config_resource_names = ConfigResourceNames.from_app_unique_id(
            self.app_unique_id
        )

        idp_config_secret_arn = aws_ssm.StringParameter.from_string_parameter_attributes(
            self,
            "ssm-idp-config-secret-arn-parameter",
            parameter_name=self.auth_setup_resource_names.idp_config_secret_arn_ssm_parameter,
            simple_name=False,
            force_dynamic_reference=True,
        )

        self.cognito_config = CognitoConfigInputs(
            cognito_user_pool_id=resolve_ssm_parameter(
                parameter_name=AuthSetupResourceNames.from_identity_provider_id(
                    identity_provider_id=self.identity_provider_id
                ).user_pool_id,
            ),
            idp_config_secret_arn=idp_config_secret_arn.string_value,
        )

        self.s3_log_lifecycle_rules = (
            EncryptedS3Construct.create_log_lifecycle_cfn_parameters(self)
        )

        self.is_demo_mode = CfnParameter(
            Stack.of(self),
            "IsDemoMode",
            type="String",
            description="Set whether demo data should be used for the frontend.",
            allowed_values=["true", "false"],
            constraint_description=("Value must be boolean (true, false)"),
            default="false",
        ).value_as_string


class ModuleOutputsConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_unique_id: str,
        solution_config_inputs: SolutionConfigInputs,
        fleet_management_api_url: str,
        ui_cf_url: str,
        ui_config_s3_path: str,
        ui_app_client_id: str,
    ) -> None:
        super().__init__(scope, construct_id)

        ssm_parameter_name_prefix = ResourcePrefix.slash_separated(
            app_unique_id=app_unique_id,
            module_name=solution_config_inputs.module_short_name,
            leading_slash=True,
        )

        # SSM Parameters
        aws_ssm.StringParameter(
            self,
            "ssm-fleet-management-api-url",
            string_value=fleet_management_api_url,
            description="Fleet Management API URL for CMS UI",
            parameter_name=ResourceName.slash_separated(
                prefix=ssm_parameter_name_prefix, name="fleet-management-api/url"
            ),
            simple_name=False,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-cms-ui-url",
            string_value=ui_cf_url,
            description="CMS UI URL",
            parameter_name=ResourceName.slash_separated(
                prefix=ssm_parameter_name_prefix, name="deployment/url"
            ),
            simple_name=False,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-cms-ui-config-path",
            string_value=ui_config_s3_path,
            description="CMS UI Config S3 Path",
            parameter_name=ResourceName.slash_separated(
                prefix=ssm_parameter_name_prefix, name="deployment/config-path"
            ),
            simple_name=False,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-cms-ui-app-client-id",
            string_value=ui_app_client_id,
            description="CMS UI App Client Id",
            parameter_name=ResourceName.slash_separated(
                prefix=ssm_parameter_name_prefix, name="auth-app-client/id"
            ),
            simple_name=False,
        )

        CfnOutput(
            self,
            "output-cms-ui-url",
            description="URL for the CMS UI",
            value=ui_cf_url,
        )

        CfnOutput(
            self,
            "output-cms-ui-config-path",
            description="S3 URI for the CMS UI Config",
            value=ui_config_s3_path,
        )
