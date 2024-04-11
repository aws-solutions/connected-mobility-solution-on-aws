# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json
import os
from functools import _lru_cache_wrapper
from typing import Any, Dict, Generator, List
from unittest.mock import patch

# Third Party Libraries
import pytest
import responses
from moto import mock_aws
from responses import matchers

# AWS Libraries
import boto3

# Connected Mobility Solution on AWS
from ....handlers.authorization_code_exchange_lambda.function import main
from .fixture_shared_jwt_mocks import (
    TEST_AUTH_RESOURCE_NAMES_CLASS,
    TEST_IDENTITY_PROVIDER_ID,
    TEST_USER_CLIENT_ID,
    VALID_ACCESS_TOKEN_KID,
    VALID_ID_TOKEN_KID,
    tokens_and_keys,
)

# Authorization Code Exchange Constants
TEST_AUTHORIZATION_CODE = "751a8f4b-9302-476c-88f0-539c520dc7d1"
TEST_CODE_VERIFIER = "authentication-test-code-verifier-123456789123456789123456789"
TEST_REDIRECT_URI = "https://localhost/test"
TEST_USER_CLIENT_SECRET = "test-user-client-secret"  # nosec
EXPECTED_REQUEST_BODY = {
    "grant_type": "authorization_code",
    "client_id": TEST_USER_CLIENT_ID,
    "client_secret": TEST_USER_CLIENT_SECRET,
    "redirect_uri": TEST_REDIRECT_URI,
    "code": TEST_AUTHORIZATION_CODE,
    "code_verifier": TEST_CODE_VERIFIER,
}
TEST_TOKEN_ENDPOINT = "https://cms-test-domain-prefix.auth.test-region-1.amazoncognito.com/oauth2/token"  # nosec

# =============== AUTOUSE ===============
@pytest.fixture(autouse=True)
def fixture_authorization_code_exchange_clear_lru_caches() -> None:
    cached_functions: List[_lru_cache_wrapper[Any]] = [
        main.get_cached_authorization_code_flow_config,
    ]
    for function in cached_functions:
        function.cache_clear()


# =============== ENVIRONMENT ===============
@pytest.fixture(name="mock_authorization_code_exchange_environment_valid")
def fixture_mock_authorization_code_exchange_environment_valid() -> Generator[
    None, None, None
]:
    env_vars = os.environ.copy()
    env_vars.update(
        {
            "USER_AGENT_STRING": "test-user-agent-string",
            "IDENTITY_PROVIDER_ID": TEST_IDENTITY_PROVIDER_ID,
        }
    )
    with patch.dict(os.environ, env_vars):
        yield


# =============== EVENT ===============
@pytest.fixture(name="authorization_code_exchange_event_valid", scope="module")
def fixture_authorization_code_exchange_event_valid() -> Dict[str, Any]:
    return {
        "AuthorizationCode": TEST_AUTHORIZATION_CODE,
        "CodeVerifier": TEST_CODE_VERIFIER,
        "RedirectUri": TEST_REDIRECT_URI,
    }


# =============== TOKENS ===============
@pytest.fixture(name="mock_tokens_endpoint_valid_tokens")
def fixture_mock_tokens_endpoint_valid_tokens() -> Generator[None, None, None]:
    valid_user_tokens = {
        "access_token": tokens_and_keys[VALID_ACCESS_TOKEN_KID]["token"],
        "id_token": tokens_and_keys[VALID_ID_TOKEN_KID]["token"],
        "refresh_token": "test-refresh-token",
        "token_use": "Bearer",
        "expires_in": 3600,
    }

    with responses.RequestsMock() as mock:
        mock.post(
            url=TEST_TOKEN_ENDPOINT,
            json=valid_user_tokens,
            status=200,
            match=[matchers.urlencoded_params_matcher(EXPECTED_REQUEST_BODY)],
        )
        yield


# =============== BOTO ===============
@pytest.fixture(
    name="authorization_code_exchange_idp_config_secret_string_valid", scope="module"
)
def fixture_authorization_code_exchange_idp_config_secret_string_valid() -> str:
    authorization_code_exchange_idp_config_json: dict[str, str] = {}
    authorization_code_exchange_idp_config_json["token_endpoint"] = TEST_TOKEN_ENDPOINT
    authorization_code_exchange_idp_config_json["client_id"] = TEST_USER_CLIENT_ID
    authorization_code_exchange_idp_config_json[
        "client_secret"
    ] = TEST_USER_CLIENT_SECRET

    return json.dumps(authorization_code_exchange_idp_config_json)


@pytest.fixture(name="mock_authorization_code_exchange_idp_config_valid")
def fixture_mock_authorization_code_exchange_idp_config_valid(
    authorization_code_exchange_idp_config_secret_string_valid: str,
) -> Generator[str, None, None]:
    with mock_aws():
        secretsmanager_client = boto3.client("secretsmanager")
        secret_arn = secretsmanager_client.create_secret(
            Name=TEST_AUTH_RESOURCE_NAMES_CLASS.authorization_code_flow_config_secret,
            SecretString=authorization_code_exchange_idp_config_secret_string_valid,
        )["ARN"]

        ssm_client = boto3.client("ssm")
        ssm_client.put_parameter(
            Name=TEST_AUTH_RESOURCE_NAMES_CLASS.authorization_code_flow_config_secret_arn_ssm_parameter,
            Value=secret_arn,
            Type="String",
        )

        yield secret_arn


@pytest.fixture(name="mock_authorization_code_exchange_idp_config_invalid_json")
def fixture_mock_authorization_code_exchange_idp_config_invalid_json() -> Generator[
    str, None, None
]:
    with mock_aws():
        secretsmanager_client = boto3.client("secretsmanager")
        secret_arn = secretsmanager_client.create_secret(
            Name=TEST_AUTH_RESOURCE_NAMES_CLASS.authorization_code_flow_config_secret,
            SecretString="Not a valid json string",
        )["ARN"]

        ssm_client = boto3.client("ssm")
        ssm_client.put_parameter(
            Name=TEST_AUTH_RESOURCE_NAMES_CLASS.authorization_code_flow_config_secret_arn_ssm_parameter,
            Value=secret_arn,
            Type="String",
        )

        yield secret_arn
