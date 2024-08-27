# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# AWS Libraries
from aws_cdk import Duration, RemovalPolicy, Stack, aws_cognito
from constructs import Construct

# Connected Mobility Solution on AWS
from .module_integration import ModuleInputsConstruct


class UsersConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        module_inputs_construct: ModuleInputsConstruct,
    ) -> None:
        super().__init__(scope, construct_id)

        cognito_id = module_inputs_construct.stack_config.identity_provider_id

        self.user_pool = aws_cognito.UserPool(
            self,
            "user-pool",
            user_pool_name=f"{cognito_id}-user-pool",
            advanced_security_mode=aws_cognito.AdvancedSecurityMode.ENFORCED,
            removal_policy=RemovalPolicy.DESTROY,
            sign_in_aliases=aws_cognito.SignInAliases(
                email=True,
                username=True,
            ),
            standard_attributes=aws_cognito.StandardAttributes(
                email=aws_cognito.StandardAttribute(required=True, mutable=True),
                phone_number=aws_cognito.StandardAttribute(
                    required=False, mutable=False
                ),
                fullname=aws_cognito.StandardAttribute(required=False, mutable=False),
                preferred_username=aws_cognito.StandardAttribute(
                    required=False, mutable=True
                ),
                timezone=aws_cognito.StandardAttribute(required=False, mutable=True),
            ),
            account_recovery=aws_cognito.AccountRecovery.EMAIL_ONLY,
            mfa=aws_cognito.Mfa.REQUIRED,
            mfa_second_factor=aws_cognito.MfaSecondFactor(sms=False, otp=True),
            user_invitation=aws_cognito.UserInvitationConfig(
                email_subject=f"Invitation to join {cognito_id}!",
                email_body=(
                    "Hello {username}, you have been invited to join "
                    f"{cognito_id}"
                    ".\nYour temporary password is: {####}"
                ),
            ),
            password_policy=aws_cognito.PasswordPolicy(
                min_length=8,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True,
                temp_password_validity=Duration.days(1),
            ),
            device_tracking=aws_cognito.DeviceTracking(
                challenge_required_on_new_device=True,
                device_only_remembered_on_user_prompt=True,
            ),
        )

        user_scope = aws_cognito.ResourceServerScope(
            scope_name=f"{cognito_id}-user",
            scope_description=f"Default scope for all {cognito_id} users.",
        )

        resource_server = aws_cognito.UserPoolResourceServer(
            self,
            "user-resource-server",
            identifier=f"{cognito_id}-user-resource-server",
            user_pool=self.user_pool,
            scopes=[user_scope],
        )

        self.o_auth_settings = aws_cognito.OAuthSettings(
            flows=aws_cognito.OAuthFlows(
                authorization_code_grant=True,
            ),
            scopes=[
                aws_cognito.OAuthScope.EMAIL,
                aws_cognito.OAuthScope.OPENID,
                aws_cognito.OAuthScope.PROFILE,
                aws_cognito.OAuthScope.resource_server(resource_server, user_scope),
            ],
            callback_urls=module_inputs_construct.stack_config.callback_urls,
        )

        self.client = self.user_pool.add_client(
            "user-client",
            user_pool_client_name=f"{cognito_id}-users-client",
            supported_identity_providers=[
                aws_cognito.UserPoolClientIdentityProvider.COGNITO
            ],
            o_auth=self.o_auth_settings,
            auth_flows=aws_cognito.AuthFlow(
                user_srp=True,
            ),
            refresh_token_validity=Duration.days(1),
            generate_secret=True,
        )

        cognito_domain = aws_cognito.CognitoDomainOptions(
            domain_prefix=f"{cognito_id}-{Stack.of(self).account}"  # Append account-id because Cognito domains have to be unique within a region
        )

        self.user_pool_domain = self.user_pool.add_domain(
            "user-pool-cognito-domain", cognito_domain=cognito_domain
        )
