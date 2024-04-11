# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json

# AWS Libraries
from aws_cdk import CfnCondition, Fn, RemovalPolicy, SecretValue, Stack
from constructs import Construct

# CMS Common Library
from cms_common.resource_names.auth import AuthResourceNames

# Connected Mobility Solution on AWS
from .cognito import CognitoConstruct
from .module_integration import ModuleInputsConstruct
from .optionally_existing_secret import OptionallyExistingSecret


class Configurations(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        cognito_construct: CognitoConstruct,
        should_populate_secrets_condition: CfnCondition,
        module_inputs_construct: ModuleInputsConstruct,
    ) -> None:
        super().__init__(scope, construct_id)

        auth_resource_names = AuthResourceNames.from_identity_provider_id(
            module_inputs_construct.stack_config.identity_provider_id
        )

        cognito_domain_prefix = (
            cognito_construct.users_construct.user_pool_domain.domain_name
        )

        # Used for: JWT Validation of users and services
        # Standard: OAuth OpenID Connect
        all_unique_scopes = list(cognito_construct.users_construct.o_auth_settings.scopes)  # type: ignore[arg-type]
        all_unique_scopes.extend(
            scope
            for scope in list(cognito_construct.services_construct.o_auth_settings.scopes)  # type: ignore[arg-type]
            if scope not in all_unique_scopes
        )
        idp_config_json = Fn.condition_if(
            should_populate_secrets_condition.logical_id,
            value_if_true=json.dumps(
                {
                    "iss_domain": f"cognito-idp.{cognito_construct.users_construct.user_pool.stack.region}.amazonaws.com/{cognito_construct.users_construct.user_pool.user_pool_id}",
                    "alternate_aud_key": "client_id",  # Cognito uses `client_id` instead of `aud` for access tokens.
                    "auds": [  # List since a specific aud does not need to specified when validating, only a valid aud.
                        cognito_construct.users_construct.client.user_pool_client_id,
                        cognito_construct.services_construct.client.user_pool_client_id,
                    ],
                    "scopes": [scope.scope_name for scope in all_unique_scopes],
                }
            ),
            value_if_false=json.dumps(
                {
                    "iss_domain": "",
                    "alternate_aud_key": "",
                    "auds": [],
                    "scopes": [],
                }
            ),
        ).to_string()

        self.idp_config_secret = OptionallyExistingSecret(
            self,
            "idp-config",
            description="IdP configurations needed to perform JWT validation for OAuth OpenID Connect auth tokens.",
            removal_policy=RemovalPolicy.DESTROY,
            secret_name=auth_resource_names.idp_config_secret,
            secret_string_value=SecretValue.unsafe_plain_text(  # Safe usage. No secret values exposed in template.
                idp_config_json
            ),
            override_existing_secret_arn=module_inputs_construct.stack_config.should_create_cognito_resources,
            optional_existing_secret_arn=module_inputs_construct.stack_config.idp_config_secret_arn,
        )

        # Used for: Client Credentials flow for services
        # Standard: OAuth OpenID Connect
        # NOTE: The json configs access the client_secret property of the UserPoolClient resource. This is implemented into CDK via a custom resource
        #       which gathers the client_secret. This custom resource is not wrapped in a VPC, causing limitations for this module with mirror world.
        #       One potential solution is to remove this reference, and allow the customer to populate the client_secret config value themselves.
        #       Another is to investigate retrieving the ClientSecret manually in the CfnTemplate utilizing Fn::GetAtt: ['CognitoUserPoolClient', 'ClientSecret']
        service_client_config_json = Fn.condition_if(
            should_populate_secrets_condition.logical_id,
            value_if_true=json.dumps(
                {
                    "token_endpoint": f"https://{cognito_domain_prefix}.auth.{Stack.of(cognito_construct.users_construct).region}.amazoncognito.com/oauth2/token",
                    "client_id": cognito_construct.services_construct.client.user_pool_client_id,
                    "client_secret": SecretValue.unsafe_unwrap(  # This is safe because it is a ref in the template and therefore does not expose the secret
                        cognito_construct.services_construct.client.user_pool_client_secret
                    ),
                    "audience": "",  # Cognito /authorize endpoint does not require an audience parameter during the client credentials flow.
                }
            ),
            value_if_false=json.dumps(
                {
                    "token_endpoint": "",
                    "client_id": "",
                    "client_secret": "",
                    "audience": "",  # Some IdPs require an audience parameter sent to the /authorize endpoint during the client credentials flow.
                },
            ),
        ).to_string()

        self.service_client_config_secret = OptionallyExistingSecret(
            self,
            "service-client-config",
            description="Client configurations needed for services to execute the Client Credentials flow, and be granted access tokens.",
            removal_policy=RemovalPolicy.DESTROY,
            secret_name=auth_resource_names.client_config_secret,
            secret_string_value=SecretValue.unsafe_plain_text(  # Safe usage. No values exposed in template.
                service_client_config_json
            ),
            override_existing_secret_arn=module_inputs_construct.stack_config.should_create_cognito_resources,
            optional_existing_secret_arn=module_inputs_construct.stack_config.service_client_config_secret_arn,
        )

        # Used by: CMS Authorization Code Flow Exchange Lambda
        # Standard: OAuth OpenId Connect
        authorization_code_exchange_config_json = Fn.condition_if(
            should_populate_secrets_condition.logical_id,
            value_if_true=json.dumps(
                {
                    "token_endpoint": f"https://{cognito_domain_prefix}.auth.{Stack.of(cognito_construct.users_construct).region}.amazoncognito.com/oauth2/token",
                    "client_id": cognito_construct.users_construct.client.user_pool_client_id,
                    "client_secret": SecretValue.unsafe_unwrap(  # Safe usage. client_secret is a Cfn Ref in the template and therefore does not expose the secret value.
                        cognito_construct.users_construct.client.user_pool_client_secret
                    ),
                }
            ),
            value_if_false=json.dumps(
                {
                    "token_endpoint": "",
                    "client_id": "",
                    "client_secret": "",
                },
            ),
        ).to_string()

        self.authorization_code_exchange_config_secret = OptionallyExistingSecret(
            self,
            "authorization-code-exchange-config",
            description="Domain and Client configurations needed to perform the authorization code flow token exchange.",
            removal_policy=RemovalPolicy.DESTROY,
            secret_name=auth_resource_names.authorization_code_flow_config_secret,
            secret_string_value=SecretValue.unsafe_plain_text(  # Safe usage. No secret values exposed in template.
                authorization_code_exchange_config_json
            ),
            override_existing_secret_arn=module_inputs_construct.stack_config.should_create_cognito_resources,
            optional_existing_secret_arn=module_inputs_construct.stack_config.authorization_code_exchange_config_secret_arn,
        )
