# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library

# Standard Library
from typing import Any, Dict

# Third Party Libraries
import pytest

# AWS Libraries
from aws_lambda_powertools.utilities.typing import LambdaContext

# Connected Mobility Solution on AWS
from ....handlers.authorization_code_exchange_lambda.function.lib.custom_exceptions import (
    AuthorizationCodeExchangeError,
)
from ....handlers.authorization_code_exchange_lambda.function.main import (
    get_user_tokens,
    handler,
)
from ..fixtures.fixture_authorization_code_exchange_lambda import (
    TEST_TOKEN_ENDPOINT,
    TEST_USER_CLIENT_SECRET,
)
from ..fixtures.fixture_shared_jwt_mocks import TEST_USER_CLIENT_ID


# =============== HANDLER SUCCESS ===============
def test_handler_valid_tokens(
    mock_authorization_code_exchange_environment_valid: None,
    mock_authorization_code_exchange_idp_config_valid: None,
    authorization_code_exchange_event_valid: Dict[str, Any],
    context: LambdaContext,
    mock_tokens_endpoint_valid_tokens: Any,
) -> None:
    response = handler(authorization_code_exchange_event_valid, context)
    assert response["message"] == "User has been authenticated. Returning user tokens."
    assert response["authenticated"] is True
    assert response["user_tokens"].get("id_token") is not None
    assert response["user_tokens"].get("access_token") is not None


# =============== HANDLER FAILURE ===============
def test_handler_invalid_environment(
    mock_authorization_code_exchange_environment_valid: None,
    authorization_code_exchange_event_valid: Dict[str, Any],
    context: LambdaContext,
) -> None:
    response = handler(authorization_code_exchange_event_valid, context)
    assert response["authenticated"] is False
    assert response["user_tokens"] is None
    assert response["message"] == "Could not exchange token. See status code."
    assert response["status_code"] == 500


def test_handler_invalid_event(
    context: LambdaContext,
) -> None:
    response = handler({"Invalid Event Key": "Invalid Event Value"}, context)
    assert response["authenticated"] is False
    assert response["user_tokens"] is None
    assert response["message"] == "Could not exchange token. See status code."
    assert response["status_code"] == 500


def test_handler_authorization_code_exchange_error(
    mock_authorization_code_exchange_environment_valid: None,
    mock_authorization_code_exchange_idp_config_valid: None,
    authorization_code_exchange_event_valid: Dict[str, Any],
    context: LambdaContext,
) -> None:
    response = handler(authorization_code_exchange_event_valid, context)
    assert response["authenticated"] is False
    assert response["user_tokens"] is None
    assert response["message"] == "Could not exchange token. See status code."
    assert response["status_code"] == 401


def test_handler_idp_config_error(
    mock_authorization_code_exchange_environment_valid: None,
    authorization_code_exchange_event_valid: Dict[str, Any],
    context: LambdaContext,
) -> None:
    response = handler(authorization_code_exchange_event_valid, context)
    assert response["authenticated"] is False
    assert response["user_tokens"] is None
    assert response["message"] == "Could not exchange token. See status code."
    assert response["status_code"] == 500


# =============== GET_USER_TOKENS ===============
def test_get_user_tokens_authorization_code_exchange_error(
    authorization_code_exchange_event_valid: Dict[str, Any],
) -> None:
    with pytest.raises(
        AuthorizationCodeExchangeError,
        match=r"Authorization Code Exchange Error: could not successfully retrieve user tokens.",
    ):
        get_user_tokens(
            token_endpoint=TEST_TOKEN_ENDPOINT,
            client_id=TEST_USER_CLIENT_ID,
            client_secret=TEST_USER_CLIENT_SECRET,
            redirect_uri=authorization_code_exchange_event_valid["RedirectUri"],
            code=authorization_code_exchange_event_valid["AuthorizationCode"],
            code_verifier=authorization_code_exchange_event_valid["CodeVerifier"],
        )
