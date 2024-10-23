# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
import pytest

# Connected Mobility Solution on AWS
from ..auth import AuthResourceNames, AuthSetupResourceNames

TEST_IDENTITY_PROVIDER_ID = "test-idp"
TEST_APP_UNIQUE_ID = "test-app"

auth_setup_resource_names = AuthSetupResourceNames.from_identity_provider_id(
    identity_provider_id=TEST_IDENTITY_PROVIDER_ID
)
auth_resource_names = AuthResourceNames.from_app_unique_id(
    app_unique_id=TEST_APP_UNIQUE_ID
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
            "service_client_config_secret",
            f"/solution/auth/{TEST_IDENTITY_PROVIDER_ID}/service-client-config/default",
        ),
        (
            "service_client_config_secret_arn_ssm_parameter",
            f"/solution/auth/{TEST_IDENTITY_PROVIDER_ID}/service-client-config/default/secret/arn",
        ),
        (
            "user_client_config_secret",
            f"/solution/auth/{TEST_IDENTITY_PROVIDER_ID}/user-client-config/default",
        ),
        (
            "user_client_config_secret_arn_ssm_parameter",
            f"/solution/auth/{TEST_IDENTITY_PROVIDER_ID}/user-client-config/default/secret/arn",
        ),
    ],
)
def test_auth_setup(attribute: str, expected_attribute_value: str) -> None:
    assert getattr(auth_setup_resource_names, attribute) == expected_attribute_value


@pytest.mark.parametrize(
    "attribute, expected_attribute_value",
    [
        (
            "token_validation_lambda_arn",
            f"/solution/{TEST_APP_UNIQUE_ID}/auth/token-validation-lambda/arn",
        ),
        (
            "authorization_code_exchange_lambda_arn",
            f"/solution/{TEST_APP_UNIQUE_ID}/auth/authorization-code-flow/authorization-code-exchange-lambda/arn",
        ),
    ],
)
def test_auth(attribute: str, expected_attribute_value: str) -> None:
    assert getattr(auth_resource_names, attribute) == expected_attribute_value
