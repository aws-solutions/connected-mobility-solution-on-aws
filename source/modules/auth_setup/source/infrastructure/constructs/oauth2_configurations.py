# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json

# AWS Libraries
from aws_cdk import CfnCondition, Fn, RemovalPolicy, SecretValue, Stack
from constructs import Construct

# CMS Common Library
from cms_common.resource_names.auth import AuthSetupResourceNames

# Connected Mobility Solution on AWS
from .cognito import CognitoConstruct
from .module_integration import ModuleInputsConstruct
from .optionally_existing_secret import OptionallyExistingSecret


class OAuth2Configurations(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        cognito_construct: CognitoConstruct,
        should_populate_secrets_condition: CfnCondition,
        module_inputs_construct: ModuleInputsConstruct,
    ) -> None:
        super().__init__(scope, construct_id)

        auth_setup_resource_names = AuthSetupResourceNames.from_identity_provider_id(
            module_inputs_construct.stack_config.identity_provider_id
        )

        cognito_domain_prefix = (
            cognito_construct.users_construct.user_pool_domain.domain_name
        )
        cognito_issuer = f"https://cognito-idp.{cognito_construct.users_construct.user_pool.stack.region}.amazonaws.com/{cognito_construct.users_construct.user_pool.user_pool_id}"
        cognito_token_endpoint = f"https://{cognito_domain_prefix}.auth.{Stack.of(cognito_construct.users_construct).region}.amazoncognito.com/oauth2/token"
        cognito_authorize_endpoint = f"https://{cognito_domain_prefix}.auth.{Stack.of(cognito_construct.users_construct).region}.amazoncognito.com/oauth2/authorize"

        cognito_auds = [  # This is a list, since a specific aud does not need to specified when validating, only the existance of any valid aud.
            cognito_construct.users_construct.client.user_pool_client_id,
            cognito_construct.services_construct.client.user_pool_client_id,
        ]

        all_unique_scopes = list(cognito_construct.users_construct.o_auth_settings.scopes)  # type: ignore[arg-type]
        all_unique_scopes.extend(
            scope
            for scope in list(cognito_construct.services_construct.o_auth_settings.scopes)  # type: ignore[arg-type]
            if scope not in all_unique_scopes
        )
        cognito_scopes = [scope.scope_name for scope in all_unique_scopes]

        # General IdP Configuration
        idp_config_json = Fn.condition_if(
            should_populate_secrets_condition.logical_id,
            value_if_true=json.dumps(
                {
                    "issuer": cognito_issuer,
                    "token_endpoint": cognito_token_endpoint,
                    "authorization_endpoint": cognito_authorize_endpoint,
                    "alternate_aud_key": "client_id",  # Cognito uses `client_id` instead of `aud` for access tokens.
                    "auds": cognito_auds,
                    "scopes": cognito_scopes,
                }
            ),
            value_if_false=json.dumps(
                {
                    "issuer": "",
                    "token_endpoint": cognito_token_endpoint,
                    "authorization_endpoint": cognito_authorize_endpoint,
                    "alternate_aud_key": "",
                    "auds": [],
                    "scopes": [],
                }
            ),
        ).to_string()

        self.idp_config_secret = OptionallyExistingSecret(
            self,
            "idp-config",
            description="IdP configurations needed to facilitate authentication and authorization via OAuth 2.0 identity providers.",
            removal_policy=RemovalPolicy.DESTROY,
            secret_name=auth_setup_resource_names.idp_config_secret,
            secret_string_value=SecretValue.unsafe_plain_text(  # Safe usage. No secret values exposed in template.
                idp_config_json
            ),
            override_existing_secret_arn=module_inputs_construct.stack_config.should_create_cognito_resources,
            optional_existing_secret_arn=module_inputs_construct.stack_config.idp_config_secret_arn,
        )

        # Service Client Configuration
        # ============================
        # NOTE: The client_secret property of the UserPoolClient resource, when accessed through CDK, is accessed via a custom resource.
        #       This custom resource is not wrapped in a VPC, causing limitations for this module with mirror world.
        #       One potential solution is to remove this reference, and allow the customer to populate the client_secret config value themselves.
        #       Another is to investigate retrieving the ClientSecret manually in the CfnTemplate utilizing Fn::GetAtt: ['CognitoUserPoolClient', 'ClientSecret']

        # NOTE: Although OAuth 2.0 standard protocol does not require an 'audience' parameter during the Client Credentials flow, it is used by certain identity providers
        #       (notably Auth0) as an extra parameter to the /token endpoint to further specify the target API or resource server for which the Access Token is being requested
        service_client_config_json = Fn.condition_if(
            should_populate_secrets_condition.logical_id,
            value_if_true=json.dumps(
                {
                    "client_id": cognito_construct.services_construct.client.user_pool_client_id,
                    "client_secret": SecretValue.unsafe_unwrap(  # This is safe because it is a ref in the template and therefore does not expose the secret
                        cognito_construct.services_construct.client.user_pool_client_secret
                    ),
                    "audience": "",
                }
            ),
            value_if_false=json.dumps(
                {
                    "client_id": "",
                    "client_secret": "",
                    "audience": "",
                },
            ),
        ).to_string()

        self.service_client_config_secret = OptionallyExistingSecret(
            self,
            "service-client-config",
            description="Service client configuration needed for OAuth 2.0 operations.",
            removal_policy=RemovalPolicy.DESTROY,
            secret_name=auth_setup_resource_names.service_client_config_secret,
            secret_string_value=SecretValue.unsafe_plain_text(  # Safe usage. No values exposed in template.
                service_client_config_json
            ),
            override_existing_secret_arn=module_inputs_construct.stack_config.should_create_cognito_resources,
            optional_existing_secret_arn=module_inputs_construct.stack_config.service_client_config_secret_arn,
        )

        # User Client Configuration
        user_client_config_json = Fn.condition_if(
            should_populate_secrets_condition.logical_id,
            value_if_true=json.dumps(
                {
                    "client_id": cognito_construct.users_construct.client.user_pool_client_id,
                    "client_secret": SecretValue.unsafe_unwrap(  # Safe usage. client_secret is a Cfn Ref in the template and therefore does not expose the secret value.
                        cognito_construct.users_construct.client.user_pool_client_secret
                    ),
                }
            ),
            value_if_false=json.dumps(
                {
                    "client_id": "",
                    "client_secret": "",
                },
            ),
        ).to_string()

        self.user_client_config_secret = OptionallyExistingSecret(
            self,
            "user-client-config",
            description="User client configuration needed for OAuth 2.0 operations.",
            removal_policy=RemovalPolicy.DESTROY,
            secret_name=auth_setup_resource_names.user_client_config_secret,
            secret_string_value=SecretValue.unsafe_plain_text(  # Safe usage. No secret values exposed in template.
                user_client_config_json
            ),
            override_existing_secret_arn=module_inputs_construct.stack_config.should_create_cognito_resources,
            optional_existing_secret_arn=module_inputs_construct.stack_config.user_client_config_secret_arn,
        )
