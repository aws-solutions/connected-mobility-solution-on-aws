# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library

# Third Party Libraries
from aws_cdk import (
    CustomResource,
    Duration,
    RemovalPolicy,
    aws_cognito,
    aws_iam,
    aws_secretsmanager,
)
from constructs import Construct

# Connected Mobility Solution on AWS
from ...config.constants import UserAuthenticationConstants
from ...handlers.custom_resource.lib.custom_resource_type_enum import CustomResourceType
from .custom_resource_lambda import CustomResourceLambdaConstruct


class CognitoConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        custom_resource_lambda_construct: CustomResourceLambdaConstruct,
    ) -> None:
        super().__init__(scope, construct_id)

        self.user_pool = aws_cognito.UserPool(
            self,
            "user-pool",
            self_sign_up_enabled=False,
            advanced_security_mode=aws_cognito.AdvancedSecurityMode.ENFORCED,
            sign_in_aliases=aws_cognito.SignInAliases(
                email=True,
                username=True,
            ),
            standard_attributes=aws_cognito.StandardAttributes(
                email=aws_cognito.StandardAttribute(required=True, mutable=False),
                fullname=aws_cognito.StandardAttribute(required=True, mutable=True),
            ),
            account_recovery=aws_cognito.AccountRecovery.EMAIL_ONLY,
            mfa=aws_cognito.Mfa.REQUIRED,
            mfa_second_factor=aws_cognito.MfaSecondFactor(sms=False, otp=True),
            user_invitation=aws_cognito.UserInvitationConfig(
                email_subject="Invitation to join Connected Mobility Solution (CMS)!",
                email_body=(
                    "Hello {username}, you have been invited to join CMS.\n"
                    "Your temporary password is {####}"
                ),
            ),
            password_policy=aws_cognito.PasswordPolicy(
                min_length=12,
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

        self.service_caller_scope = aws_cognito.ResourceServerScope(
            scope_name="cms-service",
            scope_description="Full access scope for CMS services",
        )

        self.resource_server = aws_cognito.UserPoolResourceServer(
            self,
            "resource-server",
            identifier=f"cms-resource-server-{UserAuthenticationConstants.STAGE}",
            user_pool=self.user_pool,
            scopes=[self.service_caller_scope],
        )

        self.user_app_client = self.user_pool.add_client(
            "cms-user-app-client",
            user_pool_client_name="cms-user-app-client",
            supported_identity_providers=[
                aws_cognito.UserPoolClientIdentityProvider.COGNITO
            ],
            o_auth=aws_cognito.OAuthSettings(
                flows=aws_cognito.OAuthFlows(
                    authorization_code_grant=True,
                ),
                scopes=[
                    aws_cognito.OAuthScope.EMAIL,
                    aws_cognito.OAuthScope.OPENID,
                ],
                callback_urls=["https://localhost"],
            ),
            auth_flows=aws_cognito.AuthFlow(
                user_srp=True,
            ),
            access_token_validity=Duration.hours(1),
            auth_session_validity=Duration.minutes(3),
            enable_token_revocation=True,
            id_token_validity=Duration.hours(1),
            prevent_user_existence_errors=True,
            refresh_token_validity=Duration.hours(2),
            generate_secret=True,
        )

        self.secretsmanager_user_client_secret = aws_secretsmanager.Secret(
            self,
            "secretsmanager-user-client-secret",
            description="Client secret for user app client",
            removal_policy=RemovalPolicy.DESTROY,
            secret_name=f"{UserAuthenticationConstants.STAGE}/{UserAuthenticationConstants.APP_NAME}/user-client-secret",
            secret_string_value=self.user_app_client.user_pool_client_secret,
        )

        self.service_app_client = self.user_pool.add_client(
            "cms-service-app-client",
            user_pool_client_name="cms-service-app-client",
            o_auth=aws_cognito.OAuthSettings(
                flows=aws_cognito.OAuthFlows(
                    client_credentials=True,
                ),
                scopes=[
                    aws_cognito.OAuthScope.resource_server(
                        self.resource_server, self.service_caller_scope
                    )
                ],
            ),
            access_token_validity=Duration.hours(1),
            auth_session_validity=Duration.minutes(3),
            enable_token_revocation=True,
            id_token_validity=Duration.hours(1),
            prevent_user_existence_errors=True,
            refresh_token_validity=Duration.hours(2),
            generate_secret=True,
        )

        self.secretsmanager_service_client_secret = aws_secretsmanager.Secret(
            self,
            "secretsmanager-service-client-secret",
            description="Client secret for service app client",
            removal_policy=RemovalPolicy.DESTROY,
            secret_name=f"{UserAuthenticationConstants.STAGE}/{UserAuthenticationConstants.APP_NAME}/service-client-secret",
            secret_string_value=self.service_app_client.user_pool_client_secret,
        )

        custom_resource_user_pool_policy = aws_iam.Policy(
            self,
            "userpool-policy",
            statements=[
                aws_iam.PolicyStatement(
                    actions=[
                        "cognito-idp:CreateUserPoolDomain",
                        "cognito-idp:DeleteUserPoolDomain",
                        "cognito-idp:DescribeUserPool",
                    ],
                    resources=[
                        self.user_pool.user_pool_arn,
                    ],
                )
            ],
        )
        custom_resource_lambda_construct.add_custom_resource_lambda_policy(
            policy=custom_resource_user_pool_policy,
        )

        user_pool_domain_custom_resource = CustomResource(
            self,
            "manage-user-pool-domain-custom-resource",
            service_token=custom_resource_lambda_construct.custom_resource_lambda.function_arn,
            resource_type=f"Custom::{CustomResourceType.ResourceType.MANAGE_USER_POOL_DOMAIN.value}",
            properties={
                "Resource": CustomResourceType.ResourceType.MANAGE_USER_POOL_DOMAIN.value,
                "UserPoolId": self.user_pool.user_pool_id,
            },
        )
        user_pool_domain_custom_resource.node.add_dependency(
            custom_resource_user_pool_policy
        )

        self.domain_prefix = user_pool_domain_custom_resource.get_att_string(
            "domain_prefix"
        )
