# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

# AWS Libraries
from aws_cdk import Aws, CustomResource, Duration, RemovalPolicy, aws_cognito, aws_iam
from constructs import Construct

# CMS Common Library
from cms_common.constructs.custom_resource_lambda import CustomResourceLambdaConstruct


class CognitoConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        stack_id: str,
        admin_email: str,
        cloudfront_domain_name: str,
        custom_resource_lambda_construct: CustomResourceLambdaConstruct,
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
            removal_policy=RemovalPolicy.DESTROY,
            self_sign_up_enabled=False,
            sign_in_aliases={"email": True},
            user_pool_name=f"{Aws.STACK_NAME}-user-pool",
            user_invitation={
                "email_subject": "[CMS Vehicle Simulator] Login information",
                "email_body": f"""
                    <p>
                        You are invited to join CMS Vehicle Simulator.<br />
                        https://{cloudfront_domain_name}
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

        cognito_custom_resource_policy = aws_iam.Policy(
            self,
            "custom-resource-policy",
            statements=[
                aws_iam.PolicyStatement(
                    effect=aws_iam.Effect.ALLOW,
                    actions=["cognito-idp:AdminCreateUser"],
                    resources=[self.user_pool.user_pool_arn],
                )
            ],
        )
        custom_resource_lambda_construct.add_policy_to_custom_resource_lambda(
            policy=cognito_custom_resource_policy
        )

        console_cognito_user_custom_resource = CustomResource(
            self,
            "console-cognito-user",
            service_token=custom_resource_lambda_construct.function.function_arn,
            resource_type="Custom::CreateUserpoolUser",
            properties={
                "Resource": "CreateUserpoolUser",
                "UserpoolId": self.user_pool.user_pool_id,
                "DesiredDeliveryMediums": ["EMAIL"],
                "ForceAliasCreation": "true",
                "Username": admin_email,
                "UserAttributes": [
                    {
                        "Name": "email",
                        "Value": admin_email,
                    },
                    {"Name": "email_verified", "Value": True},
                ],
            },
        )
        console_cognito_user_custom_resource.node.add_dependency(
            cognito_custom_resource_policy
        )
