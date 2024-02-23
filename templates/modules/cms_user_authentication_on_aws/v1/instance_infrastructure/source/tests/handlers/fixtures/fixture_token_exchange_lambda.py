# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
# mypy: disable-error-code="name-defined"

# Standard Library
import os
from typing import Any, Dict, Generator

# Third Party Libraries
import boto3
import pytest
import responses
from jose import jwk
from moto import mock_aws  # type: ignore[import-untyped]

# Connected Mobility Solution on AWS
from .fixture_jwt_shared import (
    EXPIRED_ACCESS_TOKEN_KID,
    EXPIRED_ID_TOKEN_KID,
    TEST_DOMAIN_PREFIX,
    TEST_LAMBDA_FUNCTION_ARN,
    TEST_USER_CLIENT_ID,
    TEST_USER_CLIENT_SECRET,
    TEST_USER_POOL_REGION,
    VALID_ACCESS_TOKEN_KID,
    VALID_ID_TOKEN_KID,
    tokens_and_keys,
)

# Store jwk.construct function to avoid patches when necessary
original_jwk_construct = jwk.construct


# VALID FIXTURES
@pytest.fixture(name="mock_env_for_token_exchange")
def mock_env_for_token_exchange() -> Generator[None, None, None]:
    with mock_aws():
        secretsmanager_client = boto3.client("secretsmanager")
        secretsmanager_client_secret = secretsmanager_client.create_secret(
            Name="test-secret", SecretString=TEST_USER_CLIENT_SECRET
        )
        os.environ.update(
            {
                "USER_CLIENT_ID": TEST_USER_CLIENT_ID,
                "USER_CLIENT_SECRET_ARN": secretsmanager_client_secret["ARN"],
                "DOMAIN_PREFIX": TEST_DOMAIN_PREFIX,
                "REDIRECT_URI": "https://localhost",
                "USER_POOL_REGION": TEST_USER_POOL_REGION,
                "TOKEN_VALIDATION_LAMBDA_ARN": TEST_LAMBDA_FUNCTION_ARN,
            }
        )
        yield


@pytest.fixture(name="mock_valid_user_pool_tokens")
def fixture_mock_valid_user_pool_tokens() -> None:
    mocked_tokens = {
        "access_token": tokens_and_keys[VALID_ACCESS_TOKEN_KID]["token"],
        "id_token": tokens_and_keys[VALID_ID_TOKEN_KID]["token"],
        "refresh_token": "test-refresh-token",
        "token_use": "Bearer",
        "expires_in": 3600,
    }

    responses.post(
        url=f"https://{TEST_DOMAIN_PREFIX}.auth.{TEST_USER_POOL_REGION}.amazoncognito.com/oauth2/token",
        json=mocked_tokens,
        status=200,
    )


@pytest.fixture(name="valid_token_exchange_event")
def fixture_valid_token_exchange_event() -> Dict[str, Any]:
    return {
        "TokenExchangeProperties": {
            "AuthorizationCode": "751a8f4b-9302-476c-88f0-539c520dc7d1",
            "CodeVerifier": "authentication-test-code-verifier-123456789123456789123456789",
        }
    }


# EXPIRED FIXTURES
@pytest.fixture(name="mock_expired_user_pool_tokens")
def fixture_mock_expired_user_pool_tokens() -> None:
    mocked_tokens = {
        "access_token": tokens_and_keys[EXPIRED_ACCESS_TOKEN_KID]["token"],
        "id_token": tokens_and_keys[EXPIRED_ID_TOKEN_KID]["token"],
        "refresh_token": "test-refresh-token",
        "token_use": "Bearer",
        "expires_in": 3600,
    }

    responses.post(
        url=f"https://{TEST_DOMAIN_PREFIX}.auth.{TEST_USER_POOL_REGION}.amazoncognito.com/oauth2/token",
        json=mocked_tokens,
        status=200,
    )
