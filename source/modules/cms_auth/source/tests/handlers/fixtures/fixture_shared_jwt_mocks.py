# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
# mypy: disable-error-code="name-defined"

# Standard Library
import time
from typing import Any, Dict, Tuple

# Third Party Libraries
import jwt
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa

# CMS Common Library
from cms_common.resource_names.auth import AuthResourceNames

# AUTH CONFIGURATION CONSTANTS
TEST_ALTERNATE_AUD_KEY = "client_id"
TEST_USER_CLIENT_ID = "test-user-client-id"
TEST_SERVICE_CLIENT_ID = "test-service-client-id"
TEST_KNOWN_AUDS = [TEST_USER_CLIENT_ID, TEST_SERVICE_CLIENT_ID]
TEST_USER_SCOPE = "test-user-scope"
TEST_SERVICE_SCOPE = "test-cms-resource-server/test-cms-scope"
TEST_KNOWN_SCOPES = [TEST_USER_SCOPE, TEST_SERVICE_SCOPE]
TEST_ISS_DOMAIN = "cognito-idp.test-user-pool-id.amazonaws.com/test-region"
TEST_IDENTITY_PROVIDER_ID = "test-idp"
TEST_AUTH_RESOURCE_NAMES_CLASS = AuthResourceNames.from_identity_provider_id(
    TEST_IDENTITY_PROVIDER_ID
)

# VALID KIDS
VALID_SERVICE_ACCESS_TOKEN_KID = "valid-service-access-token-kid"  # nosec
VALID_ID_TOKEN_KID = "valid-id-token-kid"  # nosec
VALID_ACCESS_TOKEN_KID = "valid-access-token-kid"  # nosec

# EXPIRED KIDS
EXPIRED_ID_TOKEN_KID = "expired-id-token-kid"  # nosec
EXPIRED_ACCESS_TOKEN_KID = "expired-access-token-kid"  # nosec

# INVALID KIDS
# not in JWKS list
INVALID_KID_ID_TOKEN_KID = "invalid-kid-id-token-kid"  # nosec
INVALID_KID_ACCESS_TOKEN_KID = "invalid-kid-access-token-kid"  # nosec

# INCORRECT KEY KIDS
INCORRECT_KEY_ID_TOKEN_KID = "incorrect-key-id-token-kid"  # nosec
INCORRECT_KEY_ACCESS_TOKEN_KID = "incorrect-key-access-token-kid"  # nosec

# INVALID SCOPE AND CLAIMS
INVALID_SCOPE_SERVICE_ACCESS_TOKEN_KID = (
    "invalid-scope-service-access-token-kid"  # nosec
)
INVALID_CLAIMS_ACCESS_TOKEN_KID = "invalid-claims-access-token-kid"  # nosec

# USER_POOL_JWKS
VALID_MOCKED_USER_POOL_JWKS = {
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
            "kid": INVALID_CLAIMS_ACCESS_TOKEN_KID,
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
def add_token_and_key(kid: str, key: rsa.RSAPrivateKey, token: str) -> None:
    tokens_and_keys.update({kid: {"key": key, "token": token}})


def generate_key_and_token(
    kid: str, payload: Dict[str, Any]
) -> Tuple[rsa.RSAPrivateKey, str]:
    key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )
    token = jwt.encode(
        payload=payload,
        key=key,
        algorithm="RS256",
        headers={"kid": kid},
    )
    add_token_and_key(kid, key, token)
    return key, token


# Generation functions
def generate_valid_preconstructed_tokens() -> None:
    valid_id_token_payload = {
        "exp": time.time() + 99999,
        "aud": TEST_USER_CLIENT_ID,  # Id token uses typical aud key
        "iss": f"https://{TEST_ISS_DOMAIN}",
        "token_use": "id",
        "scope": TEST_USER_SCOPE,
    }
    generate_key_and_token(VALID_ID_TOKEN_KID, valid_id_token_payload)

    valid_access_token_payload = {
        "exp": time.time() + 99999,
        TEST_ALTERNATE_AUD_KEY: TEST_USER_CLIENT_ID,  # Access token uses alternate aud key
        "iss": f"https://{TEST_ISS_DOMAIN}",
        "token_use": "access",
        "scope": TEST_USER_SCOPE,
    }
    generate_key_and_token(VALID_ACCESS_TOKEN_KID, valid_access_token_payload)


def generate_expired_preconstructed_tokens() -> None:
    expired_id_token_payload = {
        "exp": 0,
        "aud": TEST_USER_CLIENT_ID,
        "iss": f"https://{TEST_ISS_DOMAIN}",
        "token_use": "id",
        "scope": TEST_USER_SCOPE,
    }
    generate_key_and_token(EXPIRED_ID_TOKEN_KID, expired_id_token_payload)

    expired_access_token_payload = {
        "exp": 0,
        "client_id": TEST_USER_CLIENT_ID,
        "iss": f"https://{TEST_ISS_DOMAIN}",
        "token_use": "access",
        "scope": TEST_USER_SCOPE,
    }
    generate_key_and_token(EXPIRED_ACCESS_TOKEN_KID, expired_access_token_payload)


def generate_invalid_kid_preconstructed_tokens() -> None:
    invalid_kid_id_token_payload = {
        "exp": time.time() + 99999,
        "aud": TEST_USER_CLIENT_ID,
        "iss": f"https://{TEST_ISS_DOMAIN}",
        "token_use": "id",
        "scope": TEST_USER_SCOPE,
    }
    generate_key_and_token(INVALID_KID_ID_TOKEN_KID, invalid_kid_id_token_payload)

    invalid_kid_access_token_payload = {
        "exp": time.time() + 99999,
        "client_id": TEST_USER_CLIENT_ID,
        "iss": f"https://{TEST_ISS_DOMAIN}",
        "token_use": "access",
        "scope": TEST_USER_SCOPE,
    }
    generate_key_and_token(
        INVALID_KID_ACCESS_TOKEN_KID, invalid_kid_access_token_payload
    )


def generate_incorrect_key_preconstructed_tokens() -> None:
    incorrect_key_id_token_payload = {
        "exp": time.time() + 99999,
        "aud": TEST_USER_CLIENT_ID,
        "iss": f"https://{TEST_ISS_DOMAIN}",
        "token_use": "id",
        "scope": TEST_USER_SCOPE,
    }
    incorrect_key_id_token_key, incorrect_key_id_token = generate_key_and_token(
        INCORRECT_KEY_ID_TOKEN_KID, incorrect_key_id_token_payload
    )

    incorrect_key_access_token_payload = {
        "exp": time.time() + 99999,
        "client_id": TEST_USER_CLIENT_ID,
        "iss": f"https://{TEST_ISS_DOMAIN}",
        "token_use": "access",
        "scope": TEST_USER_SCOPE,
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


def generate_invalid_claims_preconstructed_tokens() -> None:
    invalid_claims_access_token_payload = {
        "exp": time.time() + 99999,
        "client_id": TEST_USER_CLIENT_ID,
        "not_iss": f"https://{TEST_ISS_DOMAIN}",
        "token_use": "access",
        "scope": TEST_USER_SCOPE,
    }
    generate_key_and_token(
        INVALID_CLAIMS_ACCESS_TOKEN_KID, invalid_claims_access_token_payload
    )


def generate_service_kids_preconstructed_tokens() -> None:
    valid_service_access_token_payload = {
        "exp": time.time() + 99999,
        "client_id": TEST_SERVICE_CLIENT_ID,  # Note that this is the service client ID instead of the user client ID, this should pass since scope is correct
        "iss": f"https://{TEST_ISS_DOMAIN}",
        "token_use": "access",
        "scope": TEST_SERVICE_SCOPE,  # Include the expected scope
    }
    generate_key_and_token(
        VALID_SERVICE_ACCESS_TOKEN_KID, valid_service_access_token_payload
    )

    invalid_scope_service_access_token_payload = {
        "exp": time.time() + 99999,
        "client_id": TEST_SERVICE_CLIENT_ID,  # Note that this is the service client ID instead of the user client ID, this should fail since scope is incorrect
        "iss": f"https://{TEST_ISS_DOMAIN}",
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
generate_invalid_claims_preconstructed_tokens()
generate_service_kids_preconstructed_tokens()
