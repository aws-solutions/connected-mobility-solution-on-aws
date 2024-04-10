# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from dataclasses import dataclass

# Connected Mobility Solution on AWS
from .module_short_names import CMSModuleShortNames


@dataclass(frozen=True)
class AuthResourceNames:
    auth_prefix: str
    idp_config_secret: str
    idp_config_secret_arn_ssm_parameter: str
    client_config_secret: str
    client_config_secret_arn_ssm_parameter: str
    authorization_code_flow_config_secret: str
    authorization_code_flow_config_secret_arn_ssm_parameter: str

    @classmethod
    def from_identity_provider_id(
        cls, identity_provider_id: str
    ) -> "AuthResourceNames":
        auth_prefix = f"/solution/{CMSModuleShortNames.AUTH}"
        auth_prefix_with_id = f"{auth_prefix}/{identity_provider_id}"
        return AuthResourceNames(
            auth_prefix=auth_prefix_with_id,
            idp_config_secret=f"{auth_prefix_with_id}/idp-config",
            idp_config_secret_arn_ssm_parameter=f"{auth_prefix_with_id}/idp-config/secret/arn",
            client_config_secret=f"{auth_prefix_with_id}/client-config/default",
            client_config_secret_arn_ssm_parameter=f"{auth_prefix_with_id}/client-config/default/secret/arn",
            authorization_code_flow_config_secret=f"{auth_prefix_with_id}/authorization-code-flow/config",
            authorization_code_flow_config_secret_arn_ssm_parameter=f"{auth_prefix_with_id}/authorization-code-flow/config/secret/arn",
        )
