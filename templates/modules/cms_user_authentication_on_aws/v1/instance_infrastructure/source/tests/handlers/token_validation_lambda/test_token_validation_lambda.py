# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
import time
from typing import Any, Dict

# Third Party Libraries
import pytest

# Connected Mobility Solution on AWS
from ....handlers.token_validation_lambda.lib.custom_exceptions import (
    TokenExpirationError,
    TokenValidationError,
    UserClaimsError,
)
from ....handlers.token_validation_lambda.main import (
    check_token_expiration,
    check_token_validity,
    check_user_claims,
    handler,
)


def test_token_validation_lambda_handler_success_id_token(
    mock_user_pool_jwks: None,
    mock_env_for_token_validation: None,
    token_validation_event_valid_id_token: Dict[str, Any],
    context: Dict[str, Any],
) -> None:
    response = handler(
        token_validation_event_valid_id_token,
        context,
    )
    assert response["isTokenValid"] is True
    assert response["message"] == "Token validation successful!"


def test_token_validation_lambda_handler_success_service_token(
    mock_user_pool_jwks: None,
    mock_env_for_token_validation: None,
    token_validation_event_valid_service_token: Dict[str, Any],
    context: Dict[str, Any],
) -> None:
    response = handler(
        token_validation_event_valid_service_token,
        context,
    )
    assert response["isTokenValid"] is True
    assert response["message"] == "Token validation successful!"


def test_token_validation_lambda_handler_invalid_event(
    mock_user_pool_jwks: None,
    mock_env_for_token_validation: None,
    invalid_token_validation_event: Dict[str, Any],
    context: Dict[str, Any],
) -> None:
    response = handler(
        invalid_token_validation_event,
        context,
    )
    assert response["isTokenValid"] is False
    assert response["message"] == "Error: event body is missing required values."


def test_token_validation_lambda_handler_invalid_token(
    mock_user_pool_jwks: None,
    mock_env_for_token_validation: None,
    token_validation_event_invalid_token: Dict[str, Any],
    context: Dict[str, Any],
) -> None:
    response = handler(
        token_validation_event_invalid_token,
        context,
    )
    assert response["isTokenValid"] is False
    assert response["message"] == "Error: token is invalid."


def test_token_validation_lambda_handler_invalid_scope_user_claims_error(
    mock_user_pool_jwks: None,
    mock_env_for_token_validation: None,
    token_validation_event_invalid_scope_service_token: Dict[str, Any],
    context: Dict[str, Any],
) -> None:
    response = handler(
        token_validation_event_invalid_scope_service_token,
        context,
    )
    assert response["isTokenValid"] is False
    assert response["message"] == "Error: user claims are invalid."


def test_token_validation_lambda_handler_decode_token_jwt_error(
    mock_user_pool_jwks: None,
    mock_env_for_token_validation: None,
    token_validation_event_jwt_error_token: Dict[str, Any],
    context: Dict[str, Any],
) -> None:
    response = handler(
        token_validation_event_jwt_error_token,
        context,
    )
    assert response["isTokenValid"] is False
    assert response["message"] == "Error: could not decode token."


def test_check_token_validity_invalid_kid(
    invalid_kid_id_token: str,
    mock_env_for_token_validation: None,
) -> None:
    with pytest.raises(
        TokenValidationError,
        match=r"Validation Failure, key id for the id token did not match the public key id for the user pool.",
    ):
        check_token_validity(invalid_kid_id_token)


def test_check_token_validity_incorrect_key(
    incorrect_key_id_token: str,
    mock_env_for_token_validation: None,
) -> None:
    with pytest.raises(
        TokenValidationError,
        match=r"Validation Failure, signature verification failed.",
    ):
        check_token_validity(incorrect_key_id_token)


def test_check_token_expiration_expired_token(
    mock_env_for_token_validation: None,
) -> None:
    expired_claim = {"exp": time.time() - 10}
    with pytest.raises(
        TokenExpirationError, match=r"Validation Failure, token is expired."
    ):
        check_token_expiration(expired_claim)


def test_check_token_expiration_missing_expiration(
    mock_env_for_token_validation: None,
) -> None:
    with pytest.raises(
        TokenExpirationError,
        match=r"Validation Failure, token did not have an expiration claim.",
    ):
        check_token_expiration({})


def test_check_user_claim_valid(
    valid_access_token_claims: Dict[str, Any],
    mock_env_for_token_validation: None,
) -> None:
    client_id = os.environ["USER_CLIENT_ID"]
    user_pool_region = os.environ["USER_POOL_REGION"]
    user_pool_id = os.environ["USER_POOL_ID"]
    check_user_claims(
        user_pool_region=user_pool_region,
        user_pool_id=user_pool_id,
        client_id=client_id,
        token_claims=valid_access_token_claims,
        token_use="access",
    )


def test_check_user_claim_missing_claim(
    valid_id_token_claims: Dict[str, Any],
    mock_env_for_token_validation: None,
) -> None:
    client_id = os.environ["USER_CLIENT_ID"]
    user_pool_region = os.environ["USER_POOL_REGION"]
    user_pool_id = os.environ["USER_POOL_ID"]
    valid_id_token_claims.pop("aud")
    with pytest.raises(
        UserClaimsError,
        match=r"Validation failure, the user tokens did not have all the expected claims.",
    ):
        check_user_claims(
            user_pool_region=user_pool_region,
            user_pool_id=user_pool_id,
            client_id=client_id,
            token_claims=valid_id_token_claims,
            token_use="id",
        )


def test_check_user_claim_incorrect_client_id(
    valid_access_token_claims: Dict[str, Any],
    mock_env_for_token_validation: None,
) -> None:
    user_pool_region = os.environ["USER_POOL_REGION"]
    user_pool_id = os.environ["USER_POOL_ID"]
    with pytest.raises(
        UserClaimsError,
        match=r"Validation Failure, user claims did not match the client id.",
    ):
        check_user_claims(
            user_pool_region=user_pool_region,
            user_pool_id=user_pool_id,
            client_id="incorrect-client-id",
            token_claims=valid_access_token_claims,
            token_use="access",
        )


def test_check_user_claim_incorrect_issuer(
    valid_id_token_claims: Dict[str, Any],
    mock_env_for_token_validation: None,
) -> None:
    client_id = os.environ["USER_CLIENT_ID"]
    user_pool_region = os.environ["USER_POOL_REGION"]
    user_pool_id = os.environ["USER_POOL_ID"]
    valid_id_token_claims["iss"] = "incorrect-issuer"
    with pytest.raises(
        UserClaimsError,
        match=r"Validation Failure, id token issuer did not match the user pool.",
    ):
        check_user_claims(
            user_pool_region=user_pool_region,
            user_pool_id=user_pool_id,
            client_id=client_id,
            token_claims=valid_id_token_claims,
            token_use="id",
        )


def test_check_user_claim_incorrect_token_use(
    valid_id_token_claims: Dict[str, Any],
    mock_env_for_token_validation: None,
) -> None:
    client_id = os.environ["USER_CLIENT_ID"]
    user_pool_region = os.environ["USER_POOL_REGION"]
    user_pool_id = os.environ["USER_POOL_ID"]
    valid_id_token_claims["token_use"] = "incorrect-token-use"
    with pytest.raises(
        UserClaimsError,
        match=r"Validation Failure, user tokens do not have the correct usage.",
    ):
        check_user_claims(
            user_pool_region=user_pool_region,
            user_pool_id=user_pool_id,
            client_id=client_id,
            token_claims=valid_id_token_claims,
            token_use="id",
        )
