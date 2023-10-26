# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

# Standard Library
from typing import TYPE_CHECKING

# Third Party Libraries
from aws_cdk import Aws, Duration, Fn, RemovalPolicy, aws_cognito
from constructs import Construct

# Connected Mobility Solution on AWS
from ...config.constants import VSConstants

if TYPE_CHECKING:
    # Connected Mobility Solution on AWS
    from ..cms_vehicle_simulator_on_aws_stack import InfrastructureCognitoStack


class CognitoConstruct(Construct):
    def __init__(
        self,
        scope: InfrastructureCognitoStack,
        stack_id: str,
    ) -> None:
        super().__init__(scope, stack_id)

        self.user_pool = aws_cognito.UserPool(
            self,
            "user-pool",
            password_policy={
                "min_length": 12,
                "require_digits": True,
                "require_lowercase": True,
                "require_symbols": True,
                "require_uppercase": True,
            },
            advanced_security_mode=aws_cognito.AdvancedSecurityMode.ENFORCED,
            removal_policy=RemovalPolicy.DESTROY,
            self_sign_up_enabled=False,
            sign_in_aliases={"email": True},
            user_pool_name=f"{Aws.STACK_NAME}-user-pool",
            user_invitation={
                "email_subject": "[CMS Vehicle Simulator] Login information",
                "email_body": f"""
                    <p>
                        You are invited to join CMS Vehicle Simulator.<br />
                        https://{Fn.import_value(f'{VSConstants.APP_NAME}-cloud-front-domain-name')}
                    </p>
                    <p>
                        Please sign in to CMS Vehicle Simulator using the temporary credentials below:<br />
                        Username: <strong>{{username}}</strong><br />Password: <strong>{{####}}</strong>
                    </p>
                """,
            },
        )

        self.user_pool_client = aws_cognito.UserPoolClient(
            self,
            "user-pool-client",
            generate_secret=False,
            o_auth=aws_cognito.OAuthSettings(
                flows=aws_cognito.OAuthFlows(authorization_code_grant=True),
            ),
            access_token_validity=Duration.hours(1),
            auth_session_validity=Duration.minutes(3),
            enable_token_revocation=True,
            id_token_validity=Duration.hours(1),
            prevent_user_existence_errors=True,
            refresh_token_validity=Duration.hours(2),
            user_pool=self.user_pool,
            user_pool_client_name=f"{Aws.STACK_NAME}-userpool-client",
        )

        self.identity_pool = aws_cognito.CfnIdentityPool(
            self,
            "identity-pool",
            allow_unauthenticated_identities=False,
            cognito_identity_providers=[
                {
                    "clientId": self.user_pool_client.user_pool_client_id,
                    "providerName": self.user_pool.user_pool_provider_name,
                    "serverSideTokenCheck": False,
                }
            ],
        )

        scope.export_value(
            self.user_pool.user_pool_id,
            name=f"{VSConstants.APP_NAME}-user-pool-id",
        )
        scope.export_value(
            self.user_pool.user_pool_arn,
            name=f"{VSConstants.APP_NAME}-user-pool-arn",
        )
        scope.export_value(
            self.user_pool_client.user_pool_client_id,
            name=f"{VSConstants.APP_NAME}-user-pool-client-id",
        )
        scope.export_value(
            self.identity_pool.ref,
            name=f"{VSConstants.APP_NAME}-identity-pool-ref",
        )
