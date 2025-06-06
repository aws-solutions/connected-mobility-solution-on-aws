# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from dataclasses import dataclass

# Connected Mobility Solution on AWS
from .module_short_names import CMSModuleShortNames


@dataclass(frozen=True)
class AuthSetupResourceNames:
    auth_prefix: str
    idp_config_secret: str
    idp_config_secret_arn_ssm_parameter: str
    service_client_config_secret: str
    service_client_config_secret_arn_ssm_parameter: str
    user_client_config_secret: str
    user_client_config_secret_arn_ssm_parameter: str
    user_pool_id: str

    @classmethod
    def from_identity_provider_id(
        cls, identity_provider_id: str
    ) -> "AuthSetupResourceNames":
        auth_prefix = f"/solution/{CMSModuleShortNames.AUTH}"
        auth_prefix_with_id = f"{auth_prefix}/{identity_provider_id}"
        return AuthSetupResourceNames(
            auth_prefix=auth_prefix_with_id,
            idp_config_secret=f"{auth_prefix_with_id}/idp-config",
            idp_config_secret_arn_ssm_parameter=f"{auth_prefix_with_id}/idp-config/secret/arn",
            service_client_config_secret=f"{auth_prefix_with_id}/service-client-config/default",
            service_client_config_secret_arn_ssm_parameter=f"{auth_prefix_with_id}/service-client-config/default/secret/arn",
            user_client_config_secret=f"{auth_prefix_with_id}/user-client-config/default",
            user_client_config_secret_arn_ssm_parameter=f"{auth_prefix_with_id}/user-client-config/default/secret/arn",
            user_pool_id=f"{auth_prefix_with_id}/user-pool/id",
        )


@dataclass(frozen=True)
class AuthResourceNames:
    token_validation_lambda_arn: str
    authorization_code_exchange_lambda_arn: str

    @classmethod
    def from_app_unique_id(cls, app_unique_id: str) -> "AuthResourceNames":
        auth_prefix = f"/solution/{app_unique_id}/{CMSModuleShortNames.AUTH}"
        return AuthResourceNames(
            token_validation_lambda_arn=f"{auth_prefix}/token-validation-lambda/arn",
            authorization_code_exchange_lambda_arn=f"{auth_prefix}/authorization-code-flow/authorization-code-exchange-lambda/arn",
        )
