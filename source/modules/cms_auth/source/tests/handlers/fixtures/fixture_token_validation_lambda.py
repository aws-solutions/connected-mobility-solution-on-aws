# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
# mypy: disable-error-code="name-defined"

# Standard Library
import json
import os
from typing import Any, Dict, Generator, List
from unittest.mock import MagicMock, patch

# Third Party Libraries
import jwt
import pytest
import responses
from moto import mock_aws

# AWS Libraries
import boto3

# CMS Common Library
from cms_common.auth.auth_configs import CMSIdPConfig

# Connected Mobility Solution on AWS
from ....handlers.token_validation_lambda.function import main
from .fixture_shared_jwt_mocks import (
    EXPIRED_ACCESS_TOKEN_KID,
    INCORRECT_KEY_ID_TOKEN_KID,
    INVALID_CLAIMS_ACCESS_TOKEN_KID,
    INVALID_KID_ID_TOKEN_KID,
    INVALID_SCOPE_SERVICE_ACCESS_TOKEN_KID,
    TEST_ALTERNATE_AUD_KEY,
    TEST_AUTH_RESOURCE_NAMES_CLASS,
    TEST_IDENTITY_PROVIDER_ID,
    TEST_ISS_DOMAIN,
    TEST_SERVICE_CLIENT_ID,
    TEST_SERVICE_SCOPE,
    TEST_USER_CLIENT_ID,
    TEST_USER_SCOPE,
    VALID_ACCESS_TOKEN_KID,
    VALID_ID_TOKEN_KID,
    VALID_MOCKED_USER_POOL_JWKS,
    VALID_SERVICE_ACCESS_TOKEN_KID,
    tokens_and_keys,
)

# =============== AUTOUSE ===============

# Conditionally mock from_jwk or call original function
def return_key(*args: Any, **kwargs: Any) -> Any:
    try:
        kid_to_construct = json.loads(args[0])["kid"]
        return tokens_and_keys[kid_to_construct]["key"].public_key()
    except TypeError:
        return original_from_jwk(*args)
    except KeyError as exception:
        raise jwt.exceptions.InvalidKeyError() from exception


algorithm_object = jwt.get_algorithm_by_name("RS256")
original_from_jwk = algorithm_object.from_jwk
algorithm_object.from_jwk = MagicMock(side_effect=return_key)  # type: ignore[method-assign]


@pytest.fixture(autouse=True)
def fixture_mock_jwk_construct() -> Generator[None, None, None]:
    with patch("jwt.get_algorithm_by_name", return_value=algorithm_object):
        yield


# Always clear caches
@pytest.fixture(autouse=True)
def fixture_token_validation_clear_lru_caches() -> None:
    main.clear_caches()


# =============== JWKs ===============
@pytest.fixture(name="mock_well_known_jwks_valid")
def fixture_mock_well_known_jwks_valid() -> Generator[None, None, None]:
    with responses.RequestsMock() as mock:
        mock.get(
            url=f"https://{TEST_ISS_DOMAIN}/.well-known/jwks.json",
            json=VALID_MOCKED_USER_POOL_JWKS,
            status=200,
        )
        yield


@pytest.fixture(name="mock_well_known_jwks_unknown_jwks")
def fixture_mock_well_known_jwks_unknown_jwks() -> Generator[None, None, None]:
    unknown_jwks = {
        "keys": [
            {
                "kid": "unknown-kid-1",
            },
            {
                "kid": "unknown-kid-2",
            },
        ]
    }

    with responses.RequestsMock() as mock:
        mock.get(
            url=f"https://{TEST_ISS_DOMAIN}/.well-known/jwks.json",
            json=unknown_jwks,
            status=200,
        )
        yield


@pytest.fixture(name="mock_well_known_jwks_invalid_key_error")
def fixture_mock_well_known_jwks_invalid_key_error() -> Generator[None, None, None]:
    with responses.RequestsMock() as mock:
        mock.get(
            url=f"https://{TEST_ISS_DOMAIN}/.well-known/jwks.json", body=KeyError()
        )
        yield


@pytest.fixture(name="mock_well_known_jwks_decode_error")
def fixture_mock_well_known_jwks_decode_error() -> Generator[None, None, None]:
    with responses.RequestsMock() as mock:
        mock.get(
            url=f"https://{TEST_ISS_DOMAIN}/.well-known/jwks.json",
            body=json.JSONDecodeError("error", "", 0),
        )
        yield


@pytest.fixture(name="valid_user_pool_jwks", scope="module")
def fixture_valid_user_pool_jwks() -> List[Dict[str, Any]]:
    return VALID_MOCKED_USER_POOL_JWKS["keys"]


@pytest.fixture(name="valid_id_token_kid", scope="module")
def fixture_valid_id_token_kid() -> Dict[str, Any]:
    return {"kid": VALID_ID_TOKEN_KID}


@pytest.fixture(name="invalid_claims_access_token_kid", scope="module")
def fixture_invalid_claims_access_token_kid() -> Dict[str, Any]:
    return {"kid": INVALID_CLAIMS_ACCESS_TOKEN_KID}


# =============== JWTs ===============
@pytest.fixture(name="valid_id_token", scope="module")
def fixture_valid_id_token() -> str:
    return str(tokens_and_keys[VALID_ID_TOKEN_KID]["token"])


@pytest.fixture(name="valid_access_token", scope="module")
def fixture_valid_access_token() -> str:
    return str(tokens_and_keys[VALID_ACCESS_TOKEN_KID]["token"])


@pytest.fixture(name="valid_service_access_token", scope="module")
def fixture_valid_service_access_token() -> str:
    return str(tokens_and_keys[VALID_SERVICE_ACCESS_TOKEN_KID]["token"])


@pytest.fixture(name="valid_id_token_claims", scope="module")
def fixture_valid_id_token_claims() -> Dict[str, Any]:
    claims: Dict[str, Any] = jwt.decode(
        tokens_and_keys[VALID_ID_TOKEN_KID]["token"],
        options={"verify_signature": False},
    )
    return claims


@pytest.fixture(name="valid_access_token_claims", scope="module")
def fixture_valid_access_token_claims() -> Dict[str, Any]:
    claims: Dict[str, Any] = jwt.decode(
        tokens_and_keys[VALID_ACCESS_TOKEN_KID]["token"],
        options={"verify_signature": False},
    )
    return claims


@pytest.fixture(name="invalid_claims_access_token", scope="module")
def fixture_invalid_claims_access_token() -> Any:
    return tokens_and_keys[INVALID_CLAIMS_ACCESS_TOKEN_KID]["token"]


@pytest.fixture(name="expired_access_token", scope="module")
def fixture_expired_access_token() -> Any:
    return tokens_and_keys[EXPIRED_ACCESS_TOKEN_KID]["token"]


@pytest.fixture(name="invalid_kid_id_token", scope="module")
def fixture_invalid_kid_id_token() -> Any:
    return tokens_and_keys[INVALID_KID_ID_TOKEN_KID]["token"]


@pytest.fixture(name="incorrect_key_id_token", scope="module")
def fixture_incorrect_key_id_token() -> Any:
    return tokens_and_keys[INCORRECT_KEY_ID_TOKEN_KID]["token"]


@pytest.fixture(name="invalid_scope_service_access_token", scope="module")
def fixture_invalid_scope_service_access_token() -> str:
    return str(tokens_and_keys[INVALID_SCOPE_SERVICE_ACCESS_TOKEN_KID]["token"])


# =============== ENVIRONMENT ===============
@pytest.fixture(name="mock_token_validation_environment_valid")
def fixture_mock_token_validation_environment_valid() -> Generator[None, None, None]:
    env_vars = os.environ.copy()
    env_vars.update(
        {
            "IDENTITY_PROVIDER_ID": TEST_IDENTITY_PROVIDER_ID,
            "USER_AGENT_STRING": "test-user-agent-string",
        }
    )
    with patch.dict(os.environ, env_vars):
        yield


# =============== EVENTS ===============
@pytest.fixture(name="token_validation_event_valid_id_token", scope="module")
def fixture_token_validation_event_valid_id_token(
    valid_id_token: str,
) -> Dict[str, Any]:
    return {
        "Token": valid_id_token,
    }


@pytest.fixture(name="token_validation_event_valid_access_token", scope="module")
def fixture_token_validation_event_valid_access_token(
    valid_access_token: str,
) -> Dict[str, Any]:
    return {
        "Token": valid_access_token,
    }


@pytest.fixture(name="token_validation_event_valid_service_token", scope="module")
def fixture_token_validation_event_valid_service_token(
    valid_service_access_token: str,
) -> Dict[str, Any]:
    return {
        "Token": valid_service_access_token,
    }


@pytest.fixture(name="token_validation_event_invalid_token_claims", scope="module")
def fixture_token_validation_event_invalid_token_claims(
    invalid_claims_access_token: str,
) -> Dict[str, Any]:
    return {
        "Token": invalid_claims_access_token,
    }


@pytest.fixture(name="token_validation_event_invalid_exp_token", scope="module")
def fixture_token_validation_event_invalid_exp_token(
    invalid_exp_access_token: str,
) -> Dict[str, Any]:
    return {
        "Token": invalid_exp_access_token,
    }


@pytest.fixture(name="token_validation_event_invalid_token", scope="module")
def fixture_token_validation_event_invalid_token(
    invalid_kid_id_token: str,
) -> Dict[str, Any]:
    return {
        "Token": invalid_kid_id_token,
    }


@pytest.fixture(name="token_validation_event_incorrect_kid_token", scope="module")
def fixture_token_validation_event_incorrect_kid_token(
    incorrect_key_id_token: str,
) -> Dict[str, Any]:
    return {
        "Token": incorrect_key_id_token,
    }


@pytest.fixture(name="token_validation_event_expired_token", scope="module")
def fixture_token_validation_event_expired_token(
    expired_access_token: str,
) -> Dict[str, Any]:
    return {
        "Token": expired_access_token,
    }


@pytest.fixture(
    name="token_validation_event_invalid_scope_service_token", scope="module"
)
def fixture_token_validation_event_invalid_scope_service_token(
    invalid_scope_service_access_token: str,
) -> Dict[str, Any]:
    return {
        "Token": invalid_scope_service_access_token,
    }


# =============== BOTO ===============
@pytest.fixture(name="token_validation_idp_config_secret_string_valid", scope="module")
def fixture_token_validation_idp_config_secret_string_valid() -> str:
    token_validation_idp_config: CMSIdPConfig = {
        "iss_domain": TEST_ISS_DOMAIN,
        "alternate_aud_key": TEST_ALTERNATE_AUD_KEY,
        "auds": [
            TEST_USER_CLIENT_ID,
            TEST_SERVICE_CLIENT_ID,
        ],
        "scopes": [TEST_USER_SCOPE, TEST_SERVICE_SCOPE],
    }
    return json.dumps(token_validation_idp_config)


@pytest.fixture(name="mock_token_validation_idp_config_valid")
def fixture_mock_token_validation_idp_config_valid(
    token_validation_idp_config_secret_string_valid: str,
) -> Generator[None, None, None]:
    with mock_aws():
        secretsmanager_client = boto3.client("secretsmanager")
        secret_arn = secretsmanager_client.create_secret(
            Name=TEST_AUTH_RESOURCE_NAMES_CLASS.idp_config_secret,
            SecretString=token_validation_idp_config_secret_string_valid,
        )["ARN"]

        ssm_client = boto3.client("ssm")
        ssm_client.put_parameter(
            Name=TEST_AUTH_RESOURCE_NAMES_CLASS.idp_config_secret_arn_ssm_parameter,
            Value=secret_arn,
            Type="String",
        )

        yield
