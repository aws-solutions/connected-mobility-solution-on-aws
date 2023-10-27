# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
# mypy: disable-error-code="name-defined"

# Standard Library
from typing import Any, Dict, Tuple

# Third Party Libraries
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jose import jwk, jwt

# COGNITO/AUTHENTICATION CONFIGURATION CONSTANTS
TEST_USER_POOL_ID = "test-user-pool-id"
TEST_USER_POOL_REGION = "test-user-pool-region"
TEST_DOMAIN_PREFIX = "test-domain-prefix"
TEST_USER_CLIENT_ID = "test-user-client-id"
TEST_USER_CLIENT_SECRET = "test-user-client-secret"  # nosec
TEST_SERVICE_CLIENT_ID = "test-service-client-id"
TEST_SERVICE_CLIENT_SECRET = "test-service-client-secret"  # nosec
TEST_NONCE = "test-nonce"
TEST_USER_POOL_ID = "test-user-pool-id"
TEST_LAMBDA_FUNCTION_ARN = "arn:aws:lambda:eu-west-1:809313241:function:test"
TEST_FORMATTED_CMS_SERVICE_SCOPE = "test-cms-resource-server/test-cms-scope"

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

# SERVICE ACCESS TOKEN KIDS
VALID_SERVICE_ACCESS_TOKEN_KID = "valid-service-access-token-kid"  # nosec
INVALID_SCOPE_SERVICE_ACCESS_TOKEN_KID = (
    "invalid-scope-service-access-token-kid"  # nosec
)

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
        {
            "kid": VALID_SERVICE_ACCESS_TOKEN_KID,
        },
        {
            "kid": INVALID_SCOPE_SERVICE_ACCESS_TOKEN_KID,
        },
    ]
}

# Map KIDs to real JWTs and JWKs. These are generated at the bottom of this file.
tokens_and_keys: Dict[str, Dict[str, Any]] = {}


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
        "aud": TEST_USER_CLIENT_ID,
        "iss": f"https://cognito-idp.{TEST_USER_POOL_REGION}.amazonaws.com/{TEST_USER_POOL_ID}",
        "token_use": "id",
        "nonce": TEST_NONCE,
    }
    generate_key_and_token(VALID_ID_TOKEN_KID, valid_id_token_payload)

    valid_access_token_payload = {
        "exp": float("inf"),
        "client_id": TEST_USER_CLIENT_ID,
        "iss": f"https://cognito-idp.{TEST_USER_POOL_REGION}.amazonaws.com/{TEST_USER_POOL_ID}",
        "token_use": "access",
    }
    generate_key_and_token(VALID_ACCESS_TOKEN_KID, valid_access_token_payload)


def generate_expired_preconstructed_tokens() -> None:
    expired_id_token_payload = {
        "exp": 0,
        "aud": TEST_USER_CLIENT_ID,
        "iss": f"https://cognito-idp.{TEST_USER_POOL_REGION}.amazonaws.com/{TEST_USER_POOL_ID}",
        "token_use": "id",
        "nonce": TEST_NONCE,
    }
    generate_key_and_token(EXPIRED_ID_TOKEN_KID, expired_id_token_payload)

    expired_access_token_payload = {
        "exp": 0,
        "client_id": TEST_USER_CLIENT_ID,
        "iss": f"https://cognito-idp.{TEST_USER_POOL_REGION}.amazonaws.com/{TEST_USER_POOL_ID}",
        "token_use": "access",
    }
    generate_key_and_token(EXPIRED_ACCESS_TOKEN_KID, expired_access_token_payload)


def generate_invalid_kid_preconstructed_tokens() -> None:
    invalid_kid_id_token_payload = {
        "exp": float("inf"),
        "aud": TEST_USER_CLIENT_ID,
        "iss": f"https://cognito-idp.{TEST_USER_POOL_REGION}.amazonaws.com/{TEST_USER_POOL_ID}",
        "token_use": "id",
        "nonce": TEST_NONCE,
    }
    generate_key_and_token(INVALID_KID_ID_TOKEN_KID, invalid_kid_id_token_payload)

    invalid_kid_access_token_payload = {
        "exp": float("inf"),
        "client_id": TEST_USER_CLIENT_ID,
        "iss": f"https://cognito-idp.{TEST_USER_POOL_REGION}.amazonaws.com/{TEST_USER_POOL_ID}",
        "token_use": "access",
    }
    generate_key_and_token(
        INVALID_KID_ACCESS_TOKEN_KID, invalid_kid_access_token_payload
    )


def generate_incorrect_key_preconstructed_tokens() -> None:
    incorrect_key_id_token_payload = {
        "exp": float("inf"),
        "aud": TEST_USER_CLIENT_ID,
        "iss": f"https://cognito-idp.{TEST_USER_POOL_REGION}.amazonaws.com/{TEST_USER_POOL_ID}",
        "token_use": "id",
        "nonce": TEST_NONCE,
    }
    incorrect_key_id_token_key, incorrect_key_id_token = generate_key_and_token(
        INCORRECT_KEY_ID_TOKEN_KID, incorrect_key_id_token_payload
    )

    incorrect_key_access_token_payload = {
        "exp": float("inf"),
        "client_id": TEST_USER_CLIENT_ID,
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


def generate_service_kids_preconstructed_tokens() -> None:
    valid_service_access_token_payload = {
        "exp": float("inf"),
        "client_id": TEST_SERVICE_CLIENT_ID,  # Note that this is the service client ID instead of the user client ID, this should pass since scope is correct
        "iss": f"https://cognito-idp.{TEST_USER_POOL_REGION}.amazonaws.com/{TEST_USER_POOL_ID}",
        "token_use": "access",
        "scope": TEST_FORMATTED_CMS_SERVICE_SCOPE,  # Include the expected scope
    }
    generate_key_and_token(
        VALID_SERVICE_ACCESS_TOKEN_KID, valid_service_access_token_payload
    )

    invalid_scope_service_access_token_payload = {
        "exp": float("inf"),
        "client_id": TEST_SERVICE_CLIENT_ID,  # Note that this is the service client ID instead of the user client ID, this should fail since scope is incorrect
        "iss": f"https://cognito-idp.{TEST_USER_POOL_REGION}.amazonaws.com/{TEST_USER_POOL_ID}",
        "token_use": "access",
        "scope": "incorrect/scope",  # Include an incorrect scope
    }
    generate_key_and_token(
        INVALID_SCOPE_SERVICE_ACCESS_TOKEN_KID,
        invalid_scope_service_access_token_payload,
    )


# Perform the generation first and only once
generate_valid_preconstructed_tokens()
generate_expired_preconstructed_tokens()
generate_invalid_kid_preconstructed_tokens()
generate_incorrect_key_preconstructed_tokens()
generate_service_kids_preconstructed_tokens()
