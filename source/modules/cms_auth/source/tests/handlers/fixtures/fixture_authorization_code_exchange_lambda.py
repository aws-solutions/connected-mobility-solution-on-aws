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

# CMS Common Library
from cms_common.auth.auth_configs import CMSClientConfig, CMSIdPConfig

# Connected Mobility Solution on AWS
from ....handlers.authorization_code_exchange_lambda.function import main
from .fixture_shared_jwt_mocks import (
    TEST_ALTERNATE_AUD_KEY,
    TEST_AUTH_SETUP_RESOURCE_NAMES_CLASS,
    TEST_AUTHORIZATION_ENDPOINT,
    TEST_IDENTITY_PROVIDER_ID,
    TEST_ISSUER,
    TEST_KNOWN_AUDS,
    TEST_KNOWN_SCOPES,
    TEST_TOKEN_ENDPOINT,
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

# =============== AUTOUSE ===============
@pytest.fixture(autouse=True)
def fixture_authorization_code_exchange_clear_lru_caches() -> None:
    cached_functions: List[_lru_cache_wrapper[Any]] = [
        main.get_cached_user_client_config,
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
@pytest.fixture(name="authorization_code_exchange_event_valid", scope="session")
def fixture_authorization_code_exchange_event_valid() -> Dict[str, Any]:
    return {
        "AuthorizationCode": TEST_AUTHORIZATION_CODE,
        "CodeVerifier": TEST_CODE_VERIFIER,
        "RedirectUri": TEST_REDIRECT_URI,
    }


# =============== TOKENS ===============
@pytest.fixture(name="mock_token_endpoint_valid_tokens")
def fixture_mock_token_endpoint_valid_tokens() -> Generator[None, None, None]:
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
@pytest.fixture(name="idp_config_secret_string_valid", scope="session")
def fixture_idp_config_secret_string_valid() -> str:
    token_validation_idp_config: CMSIdPConfig = {
        "issuer": TEST_ISSUER,
        "token_endpoint": TEST_TOKEN_ENDPOINT,
        "authorization_endpoint": TEST_AUTHORIZATION_ENDPOINT,
        "alternate_aud_key": TEST_ALTERNATE_AUD_KEY,
        "auds": TEST_KNOWN_AUDS,
        "scopes": TEST_KNOWN_SCOPES,
    }
    return json.dumps(token_validation_idp_config)


@pytest.fixture(name="mock_idp_config_valid")
def fixture_mock_idp_config_valid(
    idp_config_secret_string_valid: str,
) -> Generator[str, None, None]:
    with mock_aws():
        secretsmanager_client = boto3.client("secretsmanager")
        secret_arn = secretsmanager_client.create_secret(
            Name=TEST_AUTH_SETUP_RESOURCE_NAMES_CLASS.idp_config_secret,
            SecretString=idp_config_secret_string_valid,
        )["ARN"]

        ssm_client = boto3.client("ssm")
        ssm_client.put_parameter(
            Name=TEST_AUTH_SETUP_RESOURCE_NAMES_CLASS.idp_config_secret_arn_ssm_parameter,
            Value=secret_arn,
            Type="String",
        )

        yield secret_arn


@pytest.fixture(name="user_client_config_secret_string_valid", scope="session")
def fixture_user_client_config_secret_string_valid() -> str:
    user_client_config_json: CMSClientConfig = {
        "client_id": TEST_USER_CLIENT_ID,
        "client_secret": TEST_USER_CLIENT_SECRET,
    }

    return json.dumps(user_client_config_json)


@pytest.fixture(name="mock_user_client_config_valid")
def fixture_mock_user_client_config_valid(
    user_client_config_secret_string_valid: str,
) -> Generator[str, None, None]:
    with mock_aws():
        secretsmanager_client = boto3.client("secretsmanager")
        secret_arn = secretsmanager_client.create_secret(
            Name=TEST_AUTH_SETUP_RESOURCE_NAMES_CLASS.user_client_config_secret,
            SecretString=user_client_config_secret_string_valid,
        )["ARN"]

        ssm_client = boto3.client("ssm")
        ssm_client.put_parameter(
            Name=TEST_AUTH_SETUP_RESOURCE_NAMES_CLASS.user_client_config_secret_arn_ssm_parameter,
            Value=secret_arn,
            Type="String",
        )

        yield secret_arn


@pytest.fixture(name="mock_user_client_config_invalid_json")
def fixture_mock_user_client_config_invalid_json() -> Generator[str, None, None]:
    with mock_aws():
        secretsmanager_client = boto3.client("secretsmanager")
        secret_arn = secretsmanager_client.create_secret(
            Name=TEST_AUTH_SETUP_RESOURCE_NAMES_CLASS.user_client_config_secret,
            SecretString="Not a valid json string",
        )["ARN"]

        ssm_client = boto3.client("ssm")
        ssm_client.put_parameter(
            Name=TEST_AUTH_SETUP_RESOURCE_NAMES_CLASS.user_client_config_secret_arn_ssm_parameter,
            Value=secret_arn,
            Type="String",
        )

        yield secret_arn
