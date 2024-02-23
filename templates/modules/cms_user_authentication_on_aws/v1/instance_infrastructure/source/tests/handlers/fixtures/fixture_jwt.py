# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
# mypy: disable-error-code="name-defined"

# Standard Library
import os
from typing import Any, Dict, Generator, Tuple
from unittest.mock import patch

# Third Party Libraries
import boto3
import pytest
import requests
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwk, jwt
from moto import mock_aws  # type: ignore

# COGNITO/AUTHENTICATION CONFIGURATION CONSTANTS
TEST_USER_POOL_ID = "test-user-pool-id"
TEST_USER_POOL_REGION = "test-user-pool-region"
TEST_DOMAIN_PREFIX = "test-domain-prefix"
TEST_CLIENT_ID = "test-client-id"
TEST_CLIENT_SECRET = "test-client-secret"  # nosec
TEST_NONCE = "test-nonce"
TEST_USER_POOL_ID = "test-user-pool-id"
TEST_LAMBDA_FUNCTION_ARN = "arn:aws:lambda:eu-west-1:809313241:function:test"

# VALID KIDS
VALID_ID_TOKEN_KID = "valid-id-token-kid"  # nosec
VALID_ACCESS_TOKEN_KID = "valid-access-token-kid"  # nosec

# EXPIRED KIDS
EXPIRED_ID_TOKEN_KID = "expired-id-token-kid"  # nosec
EXPIRED_ACCESS_TOKEN_KID = "expired-access-token-kid"  # nosec

# INVALID KIDS
INVALID_KID_ID_TOKEN_KID = "invalid-kid-id-token-kid"  # nosec
INVALID_KID_ACCESS_TOKEN_KID = "invalid-kid-access-token-kid"  # nosec

# INCORRECT KEY KIDS
INCORRECT_KEY_ID_TOKEN_KID = "incorrect-key-id-token-kid"  # nosec
INCORRECT_KEY_ACCESS_TOKEN_KID = "incorrect-key-access-token-kid"  # nosec


# USER_POOL_JWKS
MOCKED_USER_POOL_JWKS = {
    "keys": [
        {
            "kid": VALID_ID_TOKEN_KID,
        },
        {
            "kid": VALID_ACCESS_TOKEN_KID,
        },
        {
            "kid": EXPIRED_ID_TOKEN_KID,
        },
        {
            "kid": EXPIRED_ACCESS_TOKEN_KID,
        },
        {
            "kid": INCORRECT_KEY_ID_TOKEN_KID,
        },
        {
            "kid": INCORRECT_KEY_ACCESS_TOKEN_KID,
        },
    ]
}

# Map KIDs to real JWTs and JWKs. These are generated at the bottom of this file.
tokens_and_keys: Dict[str, Dict[str, Any]] = {}

# Store jwk.construct function to avoid patches when necessary
original_jwk_construct = jwk.construct


# Mocked Python requests.response class:
class MockedResponse:
    def __init__(self, json_data: Any, status_code: int):
        self.json_data = json_data
        self.status_code = status_code

    def json(self) -> Any:
        return self.json_data

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise requests.exceptions.RequestException(
                "Authentication test request exception"
            )


# AUTOUSE FIXTURES
@pytest.fixture(autouse=True, scope="module")
def fixture_mock_user_pool_jwks() -> Generator[None, None, None]:
    def mock_user_pool_jwks_get(*args: str, **kwargs: Any) -> MockedResponse:
        if (
            args[0]
            == f"https://cognito-idp.{TEST_USER_POOL_REGION}.amazonaws.com/{TEST_USER_POOL_ID}/.well-known/jwks.json"
        ):
            return MockedResponse(MOCKED_USER_POOL_JWKS, 200)

        return MockedResponse(None, 400)

    with patch("requests.get", side_effect=mock_user_pool_jwks_get):
        yield


@pytest.fixture(autouse=True, scope="module")
def fixture_mock_jwk_construct() -> Generator[None, None, None]:
    def return_key(*args: Any, **kwargs: Any) -> Any:
        try:
            kid_to_construct = kwargs["key_data"]["kid"]
            return tokens_and_keys[kid_to_construct]["key"].public_key()
        except TypeError:
            return original_jwk_construct(**kwargs)

    with patch("jose.jwk.construct", side_effect=return_key):
        yield


# VALID FIXTURES
@pytest.fixture(name="mock_env_for_token_exchange")
def mock_env_for_token_exchange() -> Generator[None, None, None]:
    with mock_aws():
        secretsmanager_client = boto3.client("secretsmanager")
        secretsmanager_client_secret = secretsmanager_client.create_secret(
            Name="test-secret", SecretString=TEST_CLIENT_SECRET
        )
        os.environ.update(
            {
                "CLIENT_ID": TEST_CLIENT_ID,
                "CLIENT_SECRET_ARN": secretsmanager_client_secret["ARN"],
                "DOMAIN_PREFIX": TEST_DOMAIN_PREFIX,
                "REDIRECT_URI": "https://localhost",
                "USER_POOL_REGION": TEST_USER_POOL_REGION,
                "TOKEN_VALIDATION_LAMBDA_ARN": TEST_LAMBDA_FUNCTION_ARN,
            }
        )
        yield


@pytest.fixture(name="mock_env_for_token_validation")
def mock_env_for_token_validation() -> None:
    os.environ.update(
        {
            "USER_POOL_REGION": TEST_USER_POOL_REGION,
            "USER_POOL_ID": TEST_USER_POOL_ID,
            "CLIENT_ID": TEST_CLIENT_ID,
        }
    )


@pytest.fixture(name="mock_valid_user_pool_tokens")
def fixture_mock_valid_user_pool_tokens() -> Generator[None, None, None]:
    def mock_valid_user_pool_tokens_post(*args: str, **kwargs: Any) -> MockedResponse:
        mocked_tokens = {
            "access_token": tokens_and_keys[VALID_ACCESS_TOKEN_KID]["token"],
            "id_token": tokens_and_keys[VALID_ID_TOKEN_KID]["token"],
            "refresh_token": "test-refresh-token",
            "token_use": "Bearer",
            "expires_in": 3600,
        }

        if (
            args[0]
            == f"https://{TEST_DOMAIN_PREFIX}.auth.{TEST_USER_POOL_REGION}.amazoncognito.com/oauth2/token"
        ):
            return MockedResponse(mocked_tokens, 200)

        return MockedResponse(None, 400)

    with patch("requests.post", side_effect=mock_valid_user_pool_tokens_post):
        yield


@pytest.fixture(name="valid_id_token")
def fixture_valid_id_token() -> str:
    return str(tokens_and_keys[VALID_ID_TOKEN_KID]["token"])


@pytest.fixture(name="valid_access_token")
def fixture_valid_access_token() -> str:
    return str(tokens_and_keys[VALID_ACCESS_TOKEN_KID]["token"])


@pytest.fixture(name="valid_id_token_claims")
def fixture_valid_id_token_claims() -> Dict[str, Any]:
    return jwt.get_unverified_claims(tokens_and_keys[VALID_ID_TOKEN_KID]["token"])


@pytest.fixture(name="valid_access_token_claims")
def fixture_valid_access_token_claims() -> Dict[str, Any]:
    return jwt.get_unverified_claims(tokens_and_keys[VALID_ACCESS_TOKEN_KID]["token"])


@pytest.fixture(name="valid_token_exchange_event")
def fixture_valid_token_exchange_event() -> Dict[str, Any]:
    return {
        "TokenExchangeProperties": {
            "AuthorizationCode": "751a8f4b-9302-476c-88f0-539c520dc7d1",
            "ClientId": TEST_CLIENT_ID,
            "ClientSecret": "test-client-secret",
            "RedirectUri": "test-redirect",
            "CodeVerifier": "authentication-test-code-verifier-123456789123456789123456789",
            "DomainPrefix": TEST_DOMAIN_PREFIX,
            "nonce": TEST_NONCE,
        }
    }


# EXPIRED FIXTURES
@pytest.fixture(name="mock_expired_user_pool_tokens")
def fixture_mock_expired_user_pool_tokens() -> Generator[None, None, None]:
    def mock_expired_user_pool_tokens_post(*args: str, **kwargs: Any) -> MockedResponse:
        mocked_tokens = {
            "access_token": tokens_and_keys[EXPIRED_ACCESS_TOKEN_KID]["token"],
            "id_token": tokens_and_keys[EXPIRED_ID_TOKEN_KID]["token"],
            "refresh_token": "test-refresh-token",
            "token_use": "Bearer",
            "expires_in": 3600,
        }

        if (
            args[0]
            == f"https://{TEST_DOMAIN_PREFIX}.auth.{TEST_USER_POOL_REGION}.amazoncognito.com/oauth2/token"
        ):
            return MockedResponse(mocked_tokens, 200)

        return MockedResponse(None, 400)

    with patch("requests.post", side_effect=mock_expired_user_pool_tokens_post):
        yield


# INVALID KID FIXTURES
@pytest.fixture(name="invalid_kid_id_token")
def fixture_invalid_kid_id_token() -> Any:
    return tokens_and_keys[INVALID_KID_ID_TOKEN_KID]["token"]


# INCORRECT KEY FIXTURES
@pytest.fixture(name="incorrect_key_id_token")
def fixture_incorrect_key_id_token() -> Any:
    return tokens_and_keys[INCORRECT_KEY_ID_TOKEN_KID]["token"]


# TOKEN GENERATION
# Helper functions for generating and storing keys and tokens
def add_token_and_key(kid: str, key: jwk.Key, token: str) -> None:
    tokens_and_keys.update({kid: {"key": key, "token": token}})


def generate_key_and_token(kid: str, payload: Dict[str, Any]) -> Tuple[jwk.Key, str]:
    key_pem = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    ).private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    key = jwk.construct(key_data=key_pem, algorithm="RS256")
    token = jwt.encode(
        claims=payload,
        key=key,
        algorithm="RS256",
        headers={"kid": kid},
    )
    add_token_and_key(kid, key, token)
    return key, token


# Generation functions
def generate_valid_preconstructed_tokens() -> None:
    valid_id_token_payload = {
        "exp": float("inf"),
        "aud": TEST_CLIENT_ID,
        "iss": f"https://cognito-idp.{TEST_USER_POOL_REGION}.amazonaws.com/{TEST_USER_POOL_ID}",
        "token_use": "id",
        "nonce": TEST_NONCE,
    }
    generate_key_and_token(VALID_ID_TOKEN_KID, valid_id_token_payload)

    valid_access_token_payload = {
        "exp": float("inf"),
        "client_id": TEST_CLIENT_ID,
        "iss": f"https://cognito-idp.{TEST_USER_POOL_REGION}.amazonaws.com/{TEST_USER_POOL_ID}",
        "token_use": "access",
    }
    generate_key_and_token(VALID_ACCESS_TOKEN_KID, valid_access_token_payload)


def generate_expired_preconstructed_tokens() -> None:
    expired_id_token_payload = {
        "exp": 0,
        "aud": TEST_CLIENT_ID,
        "iss": f"https://cognito-idp.{TEST_USER_POOL_REGION}.amazonaws.com/{TEST_USER_POOL_ID}",
        "token_use": "id",
        "nonce": TEST_NONCE,
    }
    generate_key_and_token(EXPIRED_ID_TOKEN_KID, expired_id_token_payload)

    expired_access_token_payload = {
        "exp": 0,
        "client_id": TEST_CLIENT_ID,
        "iss": f"https://cognito-idp.{TEST_USER_POOL_REGION}.amazonaws.com/{TEST_USER_POOL_ID}",
        "token_use": "access",
    }
    generate_key_and_token(EXPIRED_ACCESS_TOKEN_KID, expired_access_token_payload)


def generate_invalid_kid_preconstructed_tokens() -> None:
    invalid_kid_id_token_payload = {
        "exp": float("inf"),
        "aud": TEST_CLIENT_ID,
        "iss": f"https://cognito-idp.{TEST_USER_POOL_REGION}.amazonaws.com/{TEST_USER_POOL_ID}",
        "token_use": "id",
        "nonce": TEST_NONCE,
    }
    generate_key_and_token(INVALID_KID_ID_TOKEN_KID, invalid_kid_id_token_payload)

    invalid_kid_access_token_payload = {
        "exp": float("inf"),
        "client_id": TEST_CLIENT_ID,
        "iss": f"https://cognito-idp.{TEST_USER_POOL_REGION}.amazonaws.com/{TEST_USER_POOL_ID}",
        "token_use": "access",
    }
    generate_key_and_token(
        INVALID_KID_ACCESS_TOKEN_KID, invalid_kid_access_token_payload
    )


def generate_incorrect_key_preconstructed_tokens() -> None:
    incorrect_key_id_token_payload = {
        "exp": float("inf"),
        "aud": TEST_CLIENT_ID,
        "iss": f"https://cognito-idp.{TEST_USER_POOL_REGION}.amazonaws.com/{TEST_USER_POOL_ID}",
        "token_use": "id",
        "nonce": TEST_NONCE,
    }
    incorrect_key_id_token_key, incorrect_key_id_token = generate_key_and_token(
        INCORRECT_KEY_ID_TOKEN_KID, incorrect_key_id_token_payload
    )

    incorrect_key_access_token_payload = {
        "exp": float("inf"),
        "client_id": TEST_CLIENT_ID,
        "iss": f"https://cognito-idp.{TEST_USER_POOL_REGION}.amazonaws.com/{TEST_USER_POOL_ID}",
        "token_use": "access",
    }
    incorrect_key_access_token_key, incorrect_key_access_token = generate_key_and_token(
        INCORRECT_KEY_ACCESS_TOKEN_KID, incorrect_key_access_token_payload
    )

    # Purposefully mismatch the keys and tokens
    add_token_and_key(
        INCORRECT_KEY_ID_TOKEN_KID,
        incorrect_key_access_token_key,
        incorrect_key_id_token,
    )
    add_token_and_key(
        INCORRECT_KEY_ACCESS_TOKEN_KID,
        incorrect_key_id_token_key,
        incorrect_key_access_token,
    )


# Perform the generation first and only once
generate_valid_preconstructed_tokens()
generate_expired_preconstructed_tokens()
generate_invalid_kid_preconstructed_tokens()
generate_incorrect_key_preconstructed_tokens()
