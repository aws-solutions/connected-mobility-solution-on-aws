# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from textwrap import dedent

# AWS Libraries
from aws_cdk import Duration, aws_cognito
from constructs import Construct

# Connected Mobility Solution on AWS
from .module_integration import AdminUserProperties
from .route53 import Route53Construct


class CognitoConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        admin_user: AdminUserProperties,
        email_invite_user_pool_name: str,
        route53_construct: Route53Construct,
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
                preferred_username=True,
            ),
            standard_attributes=aws_cognito.StandardAttributes(
                email=aws_cognito.StandardAttribute(required=True, mutable=False),
                fullname=aws_cognito.StandardAttribute(required=True, mutable=True),
                preferred_username=aws_cognito.StandardAttribute(
                    required=False, mutable=True
                ),
            ),
            account_recovery=aws_cognito.AccountRecovery.EMAIL_ONLY,
            mfa=aws_cognito.Mfa.REQUIRED,
            mfa_second_factor=aws_cognito.MfaSecondFactor(sms=False, otp=True),
            user_verification=aws_cognito.UserVerificationConfig(
                email_subject=f"{email_invite_user_pool_name} - Verify your email",
                email_body="Thank you for signing up!\nClick here to verify your e-mail: {##Verify Email##}",
                email_style=aws_cognito.VerificationEmailStyle.LINK,
                sms_message=f"{email_invite_user_pool_name}\nYour verification code is {{####}}",
            ),
            user_invitation=aws_cognito.UserInvitationConfig(
                email_subject=f"Invite to join {email_invite_user_pool_name}!",
                email_body=dedent(
                    f"""\
                    <p>
                    Hello {{username}}, you have been invited to join {email_invite_user_pool_name}.<br />
                    https://{route53_construct.base_domain}
                    </p>
                    <p>
                    Please sign in using the temporary credentials below:<br />
                    <pre>
                    Username: <strong>{{username}}</strong>
                    Password: <strong>{{####}}</strong>
                    </pre>
                    </p>
                    """
                ),
                sms_message=f"Hello {{username}}, your temporary password for {email_invite_user_pool_name} is {{####}}",
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

        self.oidc_client = self.user_pool.add_client(
            "oidc-client",
            generate_secret=True,
            access_token_validity=Duration.hours(1),
            auth_session_validity=Duration.minutes(3),
            enable_token_revocation=True,
            id_token_validity=Duration.hours(1),
            prevent_user_existence_errors=True,
            refresh_token_validity=Duration.hours(2),
            o_auth=aws_cognito.OAuthSettings(
                flows=aws_cognito.OAuthFlows(
                    authorization_code_grant=True,
                ),
                scopes=[aws_cognito.OAuthScope.OPENID],
                callback_urls=[
                    f"https://{route53_construct.base_domain}/api/auth/cognito/handler/frame",
                    f"https://{route53_construct.base_domain}/oauth2/idpresponse",
                ],
            ),
        )

        aws_cognito.CfnUserPoolUser(
            self,
            "admin-user",
            user_pool_id=self.user_pool.user_pool_id,
            desired_delivery_mediums=["EMAIL"],
            force_alias_creation=True,
            user_attributes=[
                {
                    "name": "email",
                    "value": admin_user.email,
                },
                {"name": "email_verified", "value": "true"},
            ],
            username=admin_user.username,
        )
