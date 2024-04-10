# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# AWS Libraries
from aws_cdk import Duration, aws_cognito
from constructs import Construct


class ServicesConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        cognito_id: str,
        user_pool: aws_cognito.UserPool,
    ) -> None:
        super().__init__(scope, construct_id)

        service_scope = aws_cognito.ResourceServerScope(
            scope_name=f"{cognito_id}-service",
            scope_description=f"Default scope for all {cognito_id} services.",
        )

        resource_server = aws_cognito.UserPoolResourceServer(
            self,
            "service-resource-server",
            identifier=f"{cognito_id}-service-resource-server",
            user_pool=user_pool,
            scopes=[service_scope],
        )

        self.o_auth_settings = aws_cognito.OAuthSettings(
            flows=aws_cognito.OAuthFlows(
                client_credentials=True,
            ),
            scopes=[
                aws_cognito.OAuthScope.resource_server(resource_server, service_scope),
            ],
        )

        self.client = user_pool.add_client(
            "service-client",
            user_pool_client_name=f"{cognito_id}-service-client",
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
