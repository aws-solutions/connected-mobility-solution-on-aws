# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import List

# Third Party Libraries
from attrs import define

# AWS Libraries
from aws_cdk import CfnParameter, Stack, aws_ssm
from constructs import Construct

# CMS Common Library
from cms_common.constructs.identity_provider_config import IdentityProviderConfig
from cms_common.resource_names.auth import AuthResourceNames


@define(auto_attribs=True, frozen=True)
class StackConfigInputs:
    identity_provider_id: str
    should_create_cognito_resources: str
    callback_urls: List[str]
    idp_config_secret_arn: str
    service_client_config_secret_arn: str
    authorization_code_exchange_config_secret_arn: str


class ModuleInputsConstruct(Construct):
    def __init__(self, scope: Construct, construct_id: str) -> None:
        super().__init__(scope, construct_id)

        identity_provider_id = IdentityProviderConfig.create_cfn_parameter(
            Stack.of(self)
        )

        should_create_cognito_resources = CfnParameter(
            Stack.of(self),
            "ShouldCreateCognitoResources",
            type="String",
            description="Boolean flag that creates resources for a default identity provider using Amazon Cognito",
            allowed_values=["true", "false"],
            constraint_description=("Value must be boolean (true, false)"),
            default="true",
        ).value_as_string

        callback_urls = CfnParameter(
            Stack.of(self),
            "CallbackUrls",
            type="CommaDelimitedList",
            description="List of callback URLs allowed for the Cognito user pool. These are the allowed redirect uris during authentication",
            default="https://example.com,https://localhost",
            allowed_pattern=r"^[a-zA_Z]{1}[a-zA-Z0-9+-.]*:\/\/(www\.)?[a-zA-Z0-9\/@%._\+~=-]*\b\/?$",
        ).value_as_list

        secret_arn_param_regex = r"(^$)|(arn:aws:secretsmanager:[a-z0-9-]+:\d{12}:secret:[a-zA-Z0-9/_+=.@-]+)"  # nosec
        secret_arn_param_constraint_description = (  # nosec
            "Value must be a valid AWS SecretsManger secret Arn"
        )

        idp_config_secret_arn = CfnParameter(
            Stack.of(self),
            "IdPConfigSecretArn",
            type="String",
            description="Secret Arn of preexisting IdP configuration json",
            allowed_pattern=secret_arn_param_regex,
            constraint_description=secret_arn_param_constraint_description,
            default="",
        ).value_as_string

        service_client_config_secret_arn = CfnParameter(
            Stack.of(self),
            "ServiceClientConfigSecretArn",
            type="String",
            description="Secret Arn of preexisting service client configuration json",
            allowed_pattern=secret_arn_param_regex,
            constraint_description=secret_arn_param_constraint_description,
            default="",
        ).value_as_string

        authorization_code_exchange_config_secret_arn = CfnParameter(
            Stack.of(self),
            "AuthorizationCodeExchangeConfigSecretArn",
            type="String",
            description="Secret Arn of preexisting authorization code exchange config json",
            allowed_pattern=secret_arn_param_regex,
            constraint_description=secret_arn_param_constraint_description,
            default="",
        ).value_as_string

        self.stack_config = StackConfigInputs(
            should_create_cognito_resources=should_create_cognito_resources,
            callback_urls=callback_urls,
            identity_provider_id=identity_provider_id,
            idp_config_secret_arn=idp_config_secret_arn,
            service_client_config_secret_arn=service_client_config_secret_arn,
            authorization_code_exchange_config_secret_arn=authorization_code_exchange_config_secret_arn,
        )


class ModuleOutputsConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        module_inputs_construct: ModuleInputsConstruct,
        idp_config_secret_arn: str,
        service_client_config_secret_arn: str,
        authorization_code_exchange_config_secret_arn: str,
    ) -> None:
        super().__init__(scope, construct_id)

        auth_resource_names = AuthResourceNames.from_identity_provider_id(
            module_inputs_construct.stack_config.identity_provider_id
        )

        aws_ssm.StringParameter(
            self,
            "ssm-idp-config-secret-arn",
            string_value=idp_config_secret_arn,
            description="Secret Arn for IdP configurations needed to perform JWT validation for OAuth OpenID Connect auth tokens.",
            parameter_name=auth_resource_names.idp_config_secret_arn_ssm_parameter,
            simple_name=True,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-service-client-config-secret-arn",
            string_value=service_client_config_secret_arn,
            description="Secret Arn for Client configurations needed for services to execute the Client Credentials flow, and be granted access tokens.",
            parameter_name=auth_resource_names.client_config_secret_arn_ssm_parameter,
            simple_name=True,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-authorization-code-exchange-config-secret-arn",
            string_value=authorization_code_exchange_config_secret_arn,
            description="Secret Arn for Domain and Client configurations needed to perform the authorization code flow token exchange.",
            parameter_name=auth_resource_names.authorization_code_flow_config_secret_arn_ssm_parameter,
            simple_name=True,
        )
