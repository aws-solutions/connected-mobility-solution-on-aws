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
from cms_common.config.regex import RegexPattern
from cms_common.constructs.identity_provider_config import IdentityProviderConfig
from cms_common.resource_names.auth import AuthResourceNames


@define(auto_attribs=True, frozen=True)
class StackConfigInputs:
    identity_provider_id: str
    should_create_cognito_resources: str
    callback_urls: List[str]
    idp_config_secret_arn: str
    service_client_config_secret_arn: str
    user_client_config_secret_arn: str


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
            default="https://example.com",
            allowed_pattern=RegexPattern.CALLBACK_URLS,
        ).value_as_list

        secret_arn_param_constraint_description = (  # nosec
            "Value must be a valid AWS SecretsManger secret Arn"
        )

        idp_config_secret_arn = CfnParameter(
            Stack.of(self),
            "IdPConfigSecretArn",
            type="String",
            description="Secret Arn of preexisting IdP configuration json",
            allowed_pattern=RegexPattern.SECRETSMANAGER_SECRET_ARN,
            constraint_description=secret_arn_param_constraint_description,
            default="",
        ).value_as_string

        service_client_config_secret_arn = CfnParameter(
            Stack.of(self),
            "ServiceClientConfigSecretArn",
            type="String",
            description="Secret Arn of preexisting service client configuration json",
            allowed_pattern=RegexPattern.SECRETSMANAGER_SECRET_ARN,
            constraint_description=secret_arn_param_constraint_description,
            default="",
        ).value_as_string

        user_client_config_secret_arn = CfnParameter(
            Stack.of(self),
            "UserClientConfigSecretArn",
            type="String",
            description="Secret Arn of preexisting user client configuration json",
            allowed_pattern=RegexPattern.SECRETSMANAGER_SECRET_ARN,
            constraint_description=secret_arn_param_constraint_description,
            default="",
        ).value_as_string

        self.stack_config = StackConfigInputs(
            should_create_cognito_resources=should_create_cognito_resources,
            callback_urls=callback_urls,
            identity_provider_id=identity_provider_id,
            idp_config_secret_arn=idp_config_secret_arn,
            service_client_config_secret_arn=service_client_config_secret_arn,
            user_client_config_secret_arn=user_client_config_secret_arn,
        )


class ModuleOutputsConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        module_inputs_construct: ModuleInputsConstruct,
        idp_config_secret_arn: str,
        service_client_config_secret_arn: str,
        user_client_config_secret_arn: str,
    ) -> None:
        super().__init__(scope, construct_id)

        auth_resource_names = AuthResourceNames.from_identity_provider_id(
            module_inputs_construct.stack_config.identity_provider_id
        )

        aws_ssm.StringParameter(
            self,
            "ssm-idp-config-secret-arn",
            string_value=idp_config_secret_arn,
            description="Secret Arn for IdP configurations needed to facilitate authentication and authorization via OAuth 2.0 identity providers.",
            parameter_name=auth_resource_names.idp_config_secret_arn_ssm_parameter,
            simple_name=False,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-service-client-config-secret-arn",
            string_value=service_client_config_secret_arn,
            description="Secret Arn for service client configuration needed for OAuth 2.0 operations.",
            parameter_name=auth_resource_names.service_client_config_secret_arn_ssm_parameter,
            simple_name=False,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-user-client-config-secret-arn",
            string_value=user_client_config_secret_arn,
            description="Secret Arn for user client configuration needed for OAuth 2.0 operations.",
            parameter_name=auth_resource_names.user_client_config_secret_arn_ssm_parameter,
            simple_name=False,
        )
