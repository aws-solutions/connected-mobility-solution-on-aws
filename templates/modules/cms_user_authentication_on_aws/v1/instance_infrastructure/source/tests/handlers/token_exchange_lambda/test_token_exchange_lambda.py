# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json
import os
from io import BytesIO

# mypy: disable-error-code=misc
from typing import Any, Dict
from unittest.mock import patch

# Third Party Libraries
import botocore
import pytest
from aws_lambda_powertools.utilities.typing import LambdaContext

# Connected Mobility Solution on AWS
from ....handlers.token_exchange_lambda.lib.custom_exceptions import (
    TokenExchangeError,
    TokenValidationError,
)
from ....handlers.token_exchange_lambda.main import (
    get_user_tokens,
    handler,
    validate_token,
)


# Flags to assert that an API call happened
class TokenExchangeAPICallBooleans:
    Invoke = False

    @classmethod
    def reset_values(cls) -> None:
        for var in vars(TokenExchangeAPICallBooleans):
            if not callable(
                getattr(TokenExchangeAPICallBooleans, var)
            ) and not var.startswith("__"):
                setattr(TokenExchangeAPICallBooleans, var, False)

    @classmethod
    def are_all_values_false(cls) -> bool:
        are_all_values_false = True
        for var in vars(TokenExchangeAPICallBooleans):
            if not callable(
                getattr(TokenExchangeAPICallBooleans, var)
            ) and not var.startswith("__"):
                if getattr(TokenExchangeAPICallBooleans, var):
                    are_all_values_false = False
                    break
        return are_all_values_false


# pylint: disable=protected-access
orig = botocore.client.BaseClient._make_api_call  # type: ignore
# pylint: disable=too-many-return-statements, inconsistent-return-statements
def mock_make_api_call(
    self: Any, operation_name: str, kwarg: Any, mock_api_responses: Any
) -> Any:
    setattr(TokenExchangeAPICallBooleans, operation_name, True)

    if operation_name in mock_api_responses:
        return mock_api_responses[operation_name]
    return orig(self, operation_name, kwarg)


def test_handler_valid_tokens(
    valid_token_exchange_event: Dict[str, Any],
    context: LambdaContext,
    mock_valid_user_pool_tokens: Any,
    mock_env_for_token_exchange: None,
) -> None:
    assert TokenExchangeAPICallBooleans.are_all_values_false()

    def _mock_api_calls_with_responses(
        self: Any, operation_name: str, kwarg: Any
    ) -> Any:
        lambda_payload = json.dumps(
            {
                "isTokenValid": True,
                "message": "Mocked success message",
            }
        ).encode()
        mocked_response = {
            "Invoke": {
                "Payload": botocore.response.StreamingBody(
                    BytesIO(lambda_payload), len(lambda_payload)
                )
            },
        }
        return mock_make_api_call(self, operation_name, kwarg, mocked_response)

    with patch(
        "botocore.client.BaseClient._make_api_call", new=_mock_api_calls_with_responses
    ):
        response = handler(valid_token_exchange_event, context)
    assert response["isAuthenticated"] is True
    assert response["user_tokens"]["id_token"]
    assert response["user_tokens"]["access_token"]
    assert TokenExchangeAPICallBooleans.Invoke is True


def test_handler_invalid_tokens(
    valid_token_exchange_event: Dict[str, Any],
    context: LambdaContext,
    mock_expired_user_pool_tokens: Any,
    mock_env_for_token_exchange: None,
) -> None:
    def _mock_api_calls_with_responses(
        self: Any, operation_name: str, kwarg: Any
    ) -> Any:
        lambda_payload = json.dumps(
            {
                "isTokenValid": False,
                "message": "Mocked error message",
            }
        ).encode()
        mocked_response = {
            "Invoke": {
                "Payload": botocore.response.StreamingBody(
                    BytesIO(lambda_payload), len(lambda_payload)
                )
            },
        }
        return mock_make_api_call(self, operation_name, kwarg, mocked_response)

    with patch(
        "botocore.client.BaseClient._make_api_call", new=_mock_api_calls_with_responses
    ):
        response = handler(valid_token_exchange_event, context)
    assert response["isAuthenticated"] is False
    assert "user_tokens" not in response
    assert TokenExchangeAPICallBooleans.Invoke is True


def test_handler_invalid_event(
    context: LambdaContext,
    mock_valid_user_pool_tokens: Any,
    mock_env_for_token_exchange: None,
) -> None:
    response = handler({}, context)
    assert response["isAuthenticated"] is False
    assert "user_tokens" not in response


def test_get_user_tokens_request_exception(
    valid_token_exchange_event: Dict[str, Any],
    mock_valid_user_pool_tokens: Any,
    mock_env_for_token_exchange: None,
) -> None:
    client_id = os.environ["USER_CLIENT_ID"]
    client_secret = "test-client-secret"
    redirect_uri = os.environ["REDIRECT_URI"]
    code = valid_token_exchange_event["TokenExchangeProperties"]["AuthorizationCode"]
    code_verifier = valid_token_exchange_event["TokenExchangeProperties"][
        "CodeVerifier"
    ]
    domain_prefix = "NOT_THE_CORRECT_DOMAIN_PREFIX"
    user_pool_region = "NOT_THE_CORRECT_REGION"
    with pytest.raises(
        TokenExchangeError,
        match=r"Could not successfully retrieve user tokens.",
    ):
        get_user_tokens(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            code=code,
            code_verifier=code_verifier,
            domain_prefix=domain_prefix,
            user_pool_region=user_pool_region,
        )


def test_validate_token_success(
    mock_env_for_token_exchange: None,
) -> None:
    def _mock_api_calls_with_responses(
        self: Any, operation_name: str, kwarg: Any
    ) -> Any:
        lambda_payload = json.dumps(
            {
                "isTokenValid": True,
                "message": "Mocked success message",
            }
        ).encode()
        mocked_response = {
            "Invoke": {
                "Payload": botocore.response.StreamingBody(
                    BytesIO(lambda_payload), len(lambda_payload)
                )
            },
        }
        return mock_make_api_call(self, operation_name, kwarg, mocked_response)

    with patch(
        "botocore.client.BaseClient._make_api_call", new=_mock_api_calls_with_responses
    ):
        validate_token(token="test_token", token_use="id", client_id="test_client_id")


def test_validate_token_invalid_exception(
    mock_env_for_token_exchange: None,
) -> None:
    def _mock_api_calls_with_responses(
        self: Any, operation_name: str, kwarg: Any
    ) -> Any:
        lambda_payload = json.dumps(
            {
                "isTokenValid": False,
                "message": "Mocked error message",
            }
        ).encode()
        mocked_response = {
            "Invoke": {
                "Payload": botocore.response.StreamingBody(
                    BytesIO(lambda_payload), len(lambda_payload)
                )
            },
        }
        return mock_make_api_call(self, operation_name, kwarg, mocked_response)

    with patch(
        "botocore.client.BaseClient._make_api_call", new=_mock_api_calls_with_responses
    ):
        with pytest.raises(
            TokenValidationError,
            match=r"Token validation failed: Mocked error message",
        ):
            validate_token(
                token="test_token", token_use="id", client_id="test_client_id"
            )


def test_validate_token_missing_values_exception() -> None:
    def _mock_api_calls_with_responses(
        self: Any, operation_name: str, kwarg: Any
    ) -> Any:
        lambda_payload = json.dumps(
            {
                "isTokenValid": False,
                "message": "Mocked error message",
            }
        ).encode()
        mocked_response = {
            "Invoke": {
                "Payload": botocore.response.StreamingBody(
                    BytesIO(lambda_payload), len(lambda_payload)
                )
            },
        }
        return mock_make_api_call(self, operation_name, kwarg, mocked_response)

    with patch(
        "botocore.client.BaseClient._make_api_call", new=_mock_api_calls_with_responses
    ):
        with pytest.raises(
            TokenValidationError,
            match=r"Token validation failed:",
        ):
            validate_token(
                token="test_token", token_use="id", client_id="test_client_id"
            )
