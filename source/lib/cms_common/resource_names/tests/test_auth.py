# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
import pytest

# Connected Mobility Solution on AWS
from ..auth import AuthResourceNames

TEST_IDENTITY_PROVIDER_ID = "test-idp"

auth_resource_names = AuthResourceNames.from_identity_provider_id(
    identity_provider_id=TEST_IDENTITY_PROVIDER_ID
)


@pytest.mark.parametrize(
    "attribute, expected_attribute_value",
    [
        ("auth_prefix", f"/solution/auth/{TEST_IDENTITY_PROVIDER_ID}"),
        ("idp_config_secret", f"/solution/auth/{TEST_IDENTITY_PROVIDER_ID}/idp-config"),
        (
            "idp_config_secret_arn_ssm_parameter",
            f"/solution/auth/{TEST_IDENTITY_PROVIDER_ID}/idp-config/secret/arn",
        ),
        (
            "client_config_secret",
            f"/solution/auth/{TEST_IDENTITY_PROVIDER_ID}/client-config/default",
        ),
        (
            "client_config_secret_arn_ssm_parameter",
            f"/solution/auth/{TEST_IDENTITY_PROVIDER_ID}/client-config/default/secret/arn",
        ),
        (
            "authorization_code_flow_config_secret",
            f"/solution/auth/{TEST_IDENTITY_PROVIDER_ID}/authorization-code-flow/config",
        ),
        (
            "authorization_code_flow_config_secret_arn_ssm_parameter",
            f"/solution/auth/{TEST_IDENTITY_PROVIDER_ID}/authorization-code-flow/config/secret/arn",
        ),
    ],
)
def test_auth(attribute: str, expected_attribute_value: str) -> None:
    assert getattr(auth_resource_names, attribute) == expected_attribute_value
