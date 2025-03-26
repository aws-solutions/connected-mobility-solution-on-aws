# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# AWS Libraries
from aws_cdk import Stack, aws_cognito, aws_iam, aws_location
from constructs import Construct

# Connected Mobility Solution on AWS
from .cognito_app_client import CognitoAppClientConstruct
from .module_integration import CognitoConfigInputs


class LocationMapConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_unique_id: str,
        cognito_config: CognitoConfigInputs,
        cognito_app_client: CognitoAppClientConstruct,
    ) -> None:
        super().__init__(scope, construct_id)

        self.map_name = f"{app_unique_id}-map"
        location_map = aws_location.CfnMap(
            self,
            "location-map",
            map_name=self.map_name,
            configuration={"style": "VectorEsriStreets"},
        )

        identity_provider = aws_cognito.CfnIdentityPool.CognitoIdentityProviderProperty(
            provider_name=f"cognito-idp.{Stack.of(self).region}.amazonaws.com/{cognito_config.cognito_user_pool_id}",
            client_id=cognito_app_client.cms_ui_client_id,
            server_side_token_check=False,
        )

        self.identity_pool = aws_cognito.CfnIdentityPool(
            self,
            "IdentityPool",
            identity_pool_name=f"{app_unique_id}-maps-provider",
            allow_unauthenticated_identities=False,
            cognito_identity_providers=[identity_provider],
        )

        authenticated_role = aws_iam.Role(
            self,
            "CognitoAuthenticatedRole",
            assumed_by=aws_iam.FederatedPrincipal(
                "cognito-identity.amazonaws.com",
                {
                    "StringEquals": {
                        "cognito-identity.amazonaws.com:aud": self.identity_pool.ref
                    },
                    "ForAnyValue:StringLike": {
                        "cognito-identity.amazonaws.com:amr": "authenticated"
                    },
                },
                "sts:AssumeRoleWithWebIdentity",
            ),
        )

        authenticated_role.add_to_policy(
            aws_iam.PolicyStatement(
                actions=[
                    "geo:GetMapStyleDescriptor",
                    "geo:GetMapGlyphs",
                    "geo:GetMapSprites",
                    "geo:GetMapTile",
                ],
                resources=[
                    location_map.attr_arn,
                ],
            )
        )

        aws_cognito.CfnIdentityPoolRoleAttachment(
            self,
            "identity-pool-role-attachment",
            identity_pool_id=self.identity_pool.ref,
            roles={"authenticated": authenticated_role.role_arn},
        )
