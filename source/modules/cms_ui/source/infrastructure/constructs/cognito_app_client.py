# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# AWS Libraries
from aws_cdk import Duration, aws_cognito
from constructs import Construct

# CMS Common Library
from cms_common.resource_names.module_short_names import CMSModuleShortNames

# Connected Mobility Solution on AWS
from .module_integration import ModuleInputsConstruct
from .user_interface_deployment import UserInterfaceDeploymentConstruct


class CognitoAppClientConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_unique_id: str,
        module_inputs: ModuleInputsConstruct,
        user_interface_deployment: UserInterfaceDeploymentConstruct,
    ) -> None:
        super().__init__(scope, construct_id)

        cms_user_pool = aws_cognito.UserPool.from_user_pool_id(
            self, "cms-user-pool", module_inputs.cognito_config.cognito_user_pool_id
        )

        ui_user_scope = aws_cognito.ResourceServerScope(
            scope_name=f"{app_unique_id}-ui-user",
            scope_description=f"Default scope for all {app_unique_id} UI users.",
        )

        resource_server = aws_cognito.UserPoolResourceServer(
            self,
            "user-resource-server",
            identifier=f"{app_unique_id}-{CMSModuleShortNames.UI}-user-resource-server",
            user_pool=cms_user_pool,
            scopes=[ui_user_scope],
        )

        self.supported_scopes = [
            aws_cognito.OAuthScope.EMAIL,
            aws_cognito.OAuthScope.OPENID,
            aws_cognito.OAuthScope.PROFILE,
            aws_cognito.OAuthScope.resource_server(resource_server, ui_user_scope),
        ]

        cloudfront_domain_name = (
            user_interface_deployment.cloudfront_dist.cloud_front_web_distribution.domain_name
        )

        o_auth_settings = aws_cognito.OAuthSettings(
            flows=aws_cognito.OAuthFlows(
                authorization_code_grant=True,
            ),
            scopes=self.supported_scopes,
            callback_urls=[
                f"https://{cloudfront_domain_name}",
                f"https://{cloudfront_domain_name}/callback",
            ],
        )

        cms_ui_client = cms_user_pool.add_client(
            "cms-ui-app-client",
            user_pool_client_name=f"{app_unique_id}-{CMSModuleShortNames.UI}-users-client",
            supported_identity_providers=[
                aws_cognito.UserPoolClientIdentityProvider.COGNITO
            ],
            o_auth=o_auth_settings,
            auth_flows=aws_cognito.AuthFlow(
                user_srp=True,
            ),
            refresh_token_validity=Duration.days(30),
            access_token_validity=Duration.minutes(15),
            id_token_validity=Duration.minutes(60),
            enable_token_revocation=True,
            prevent_user_existence_errors=True,
            generate_secret=False,
        )

        self.cms_ui_client_id = cms_ui_client.user_pool_client_id
