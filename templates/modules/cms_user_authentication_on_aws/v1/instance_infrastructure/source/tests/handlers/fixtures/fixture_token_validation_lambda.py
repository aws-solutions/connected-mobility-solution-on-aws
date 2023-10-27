# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
# mypy: disable-error-code="name-defined"

# Standard Library
import os
from typing import Any, Dict, Generator
from unittest.mock import patch

# Third Party Libraries
import pytest
import responses
from jose import jwk, jwt

# Connected Mobility Solution on AWS
from .fixture_jwt_shared import (
    INCORRECT_KEY_ID_TOKEN_KID,
    INVALID_KID_ID_TOKEN_KID,
    INVALID_SCOPE_SERVICE_ACCESS_TOKEN_KID,
    MOCKED_USER_POOL_JWKS,
    TEST_FORMATTED_CMS_SERVICE_SCOPE,
    TEST_SERVICE_CLIENT_ID,
    TEST_USER_CLIENT_ID,
    TEST_USER_POOL_ID,
    TEST_USER_POOL_REGION,
    VALID_ACCESS_TOKEN_KID,
    VALID_ID_TOKEN_KID,
    VALID_SERVICE_ACCESS_TOKEN_KID,
    tokens_and_keys,
)


# AUTOUSE FIXTURES
@pytest.fixture(name="mock_user_pool_jwks", scope="session")
def fixture_mock_user_pool_jwks() -> Generator[None, None, None]:
    with responses.RequestsMock() as mock:
        mock.get(
            url=f"https://cognito-idp.{TEST_USER_POOL_REGION}.amazonaws.com/{TEST_USER_POOL_ID}/.well-known/jwks.json",
            json=MOCKED_USER_POOL_JWKS,
            status=200,
        )
        yield


# Store jwk.construct function to avoid patches when necessary
original_jwk_construct = jwk.construct


@pytest.fixture(autouse=True, scope="session")
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
@pytest.fixture(name="mock_env_for_token_validation")
def mock_env_for_token_validation() -> None:
    os.environ.update(
        {
            "USER_POOL_REGION": TEST_USER_POOL_REGION,
            "USER_POOL_ID": TEST_USER_POOL_ID,
            "USER_CLIENT_ID": TEST_USER_CLIENT_ID,
            "SERVICE_CLIENT_ID": TEST_SERVICE_CLIENT_ID,
            "FORMATTED_CMS_SERVICE_SCOPE": TEST_FORMATTED_CMS_SERVICE_SCOPE,
        }
    )


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


@pytest.fixture(name="token_validation_event_valid_id_token")
def fixture_token_validation_event_valid_id_token(
    valid_id_token: str,
) -> Dict[str, Any]:
    return {"TokenValidationProperties": {"Token": valid_id_token, "TokenUse": "id"}}


# INVALID FIXTURES
@pytest.fixture(name="invalid_kid_id_token")
def fixture_invalid_kid_id_token() -> Any:
    return tokens_and_keys[INVALID_KID_ID_TOKEN_KID]["token"]


@pytest.fixture(name="incorrect_key_id_token")
def fixture_incorrect_key_id_token() -> Any:
    return tokens_and_keys[INCORRECT_KEY_ID_TOKEN_KID]["token"]


@pytest.fixture(name="invalid_token_validation_event")
def fixture_invalid_token_validation_event(valid_id_token: str) -> Dict[str, Any]:
    return {"InvalidEventProperties": {"Token": valid_id_token, "TokenUse": "id"}}


@pytest.fixture(name="token_validation_event_invalid_token")
def fixture_token_validation_event_invalid_token(
    invalid_kid_id_token: str,
) -> Dict[str, Any]:
    return {
        "TokenValidationProperties": {"Token": invalid_kid_id_token, "TokenUse": "id"}
    }


@pytest.fixture(name="token_validation_event_jwt_error_token")
def fixture_token_validation_event_jwt_error_token() -> Dict[str, Any]:
    return {
        "TokenValidationProperties": {
            "Token": "this isn't a real token that can be decoded",
            "TokenUse": "access",
        }
    }


# SERVICE TOKEN FIXTURES
@pytest.fixture(name="valid_service_access_token")
def fixture_valid_service_access_token() -> str:
    return str(tokens_and_keys[VALID_SERVICE_ACCESS_TOKEN_KID]["token"])


@pytest.fixture(name="invalid_scope_service_access_token")
def fixture_invalid_scope_service_access_token() -> str:
    return str(tokens_and_keys[INVALID_SCOPE_SERVICE_ACCESS_TOKEN_KID]["token"])


@pytest.fixture(name="token_validation_event_valid_service_token")
def fixture_token_validation_event_valid_service_token(
    valid_service_access_token: str,
) -> Dict[str, Any]:
    return {
        "TokenValidationProperties": {
            "Token": valid_service_access_token,
            "TokenUse": "access",
        }
    }


@pytest.fixture(name="token_validation_event_invalid_scope_service_token")
def fixture_token_validation_event_invalid_scope_service_token(
    invalid_scope_service_access_token: str,
) -> Dict[str, Any]:
    return {
        "TokenValidationProperties": {
            "Token": invalid_scope_service_access_token,
            "TokenUse": "access",
        }
    }
