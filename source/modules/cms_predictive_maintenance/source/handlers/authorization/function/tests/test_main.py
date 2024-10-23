# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json
from io import BytesIO
from typing import Any, Dict
from unittest.mock import patch

# AWS Libraries
import botocore
from aws_lambda_powertools.utilities.typing import LambdaContext

# Connected Mobility Solution on AWS
from ..main import handler


# Flags to assert that an API call happened
class AuthorizationAPICallBooleans:
    Invoke = False

    @classmethod
    def reset_values(cls) -> None:
        for var in vars(AuthorizationAPICallBooleans):
            if not callable(
                getattr(AuthorizationAPICallBooleans, var)
            ) and not var.startswith("__"):
                setattr(AuthorizationAPICallBooleans, var, False)

    @classmethod
    def are_all_values_false(cls) -> bool:
        are_all_values_false = True
        for var in vars(AuthorizationAPICallBooleans):
            if not callable(
                getattr(AuthorizationAPICallBooleans, var)
            ) and not var.startswith("__"):
                if getattr(AuthorizationAPICallBooleans, var):
                    are_all_values_false = False
                    break
        return are_all_values_false


# pylint: disable=protected-access
orig = botocore.client.BaseClient._make_api_call  # type: ignore


# pylint: disable=too-many-return-statements, inconsistent-return-statements
def mock_make_api_call(
    self: Any, operation_name: str, kwarg: Any, mock_api_responses: Any
) -> Any:
    setattr(AuthorizationAPICallBooleans, operation_name, True)

    if operation_name in mock_api_responses:
        return mock_api_responses[operation_name]
    return orig(self, operation_name, kwarg)


def test_authorization_handler_success(
    valid_authorization_event: Dict[str, Any],
    context: LambdaContext,
    mock_env_for_authorization: None,
    authorization_allow_policy: Dict[str, Any],
) -> None:
    assert AuthorizationAPICallBooleans.are_all_values_false()

    def _mock_api_calls_with_responses(
        self: Any, operation_name: str, kwarg: Any
    ) -> Any:
        lambda_payload = json.dumps(
            {
                "validated": True,
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
        response = handler(valid_authorization_event, context)
    assert response == authorization_allow_policy
    assert AuthorizationAPICallBooleans.Invoke is True


def test_authorization_handler_invalid_token(
    valid_authorization_event: Dict[str, Any],
    context: LambdaContext,
    mock_env_for_authorization: None,
    authorization_deny_policy: Dict[str, Any],
) -> None:
    assert AuthorizationAPICallBooleans.are_all_values_false()

    def _mock_api_calls_with_responses(
        self: Any, operation_name: str, kwarg: Any
    ) -> Any:
        lambda_payload = json.dumps(
            {
                "validated": False,
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
        response = handler(valid_authorization_event, context)
    assert response == authorization_deny_policy
    assert AuthorizationAPICallBooleans.Invoke is True


def test_authorization_handler_invalid_event(
    invalid_authorization_event: Dict[str, Any],
    context: LambdaContext,
    mock_env_for_authorization: None,
    authorization_deny_policy: Dict[str, Any],
) -> None:
    response = handler(invalid_authorization_event, context)
    assert response == authorization_deny_policy
