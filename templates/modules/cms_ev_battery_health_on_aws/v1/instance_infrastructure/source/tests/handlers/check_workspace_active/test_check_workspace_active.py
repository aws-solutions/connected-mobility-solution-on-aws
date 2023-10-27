# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0


# Standard Library
from typing import Any
from unittest.mock import patch

# Third Party Libraries
import botocore
import pytest
from aws_lambda_powertools.utilities.typing import LambdaContext

# Connected Mobility Solution on AWS
from ....handlers.check_workspace_active.main import handler


class CheckWorkspaceStatusAPICallBooleans:
    DescribeWorkspace = False

    @classmethod
    def reset_values(cls) -> None:
        for var in vars(CheckWorkspaceStatusAPICallBooleans):
            if not callable(
                getattr(CheckWorkspaceStatusAPICallBooleans, var)
            ) and not var.startswith("__"):
                setattr(CheckWorkspaceStatusAPICallBooleans, var, False)

    @classmethod
    def are_all_values_false(cls) -> bool:
        are_all_values_false = True
        for var in vars(CheckWorkspaceStatusAPICallBooleans):
            if not callable(
                getattr(CheckWorkspaceStatusAPICallBooleans, var)
            ) and not var.startswith("__"):
                if getattr(CheckWorkspaceStatusAPICallBooleans, var):
                    are_all_values_false = False
                    break
        return are_all_values_false


# pylint: disable=protected-access
orig = botocore.client.BaseClient._make_api_call  # type: ignore
# pylint: disable=too-many-return-statements, inconsistent-return-statements
def mock_make_api_call(
    self: Any, operation_name: str, kwarg: Any, mock_api_responses: Any
) -> Any:
    setattr(CheckWorkspaceStatusAPICallBooleans, operation_name, True)

    if operation_name in mock_api_responses:
        return mock_api_responses[operation_name]
    return orig(self, operation_name, kwarg)


@pytest.mark.parametrize("is_active", [True, False])
def test_handler_active(context: LambdaContext, is_active: bool) -> None:
    def _mock_api_calls_with_responses(
        self: Any, operation_name: str, kwarg: Any
    ) -> Any:
        mocked_response = {
            "DescribeWorkspace": {
                "workspace": {
                    "status": "ACTIVE" if is_active else "INACTIVE",
                },
            },
        }
        return mock_make_api_call(self, operation_name, kwarg, mocked_response)

    with patch(
        "botocore.client.BaseClient._make_api_call", new=_mock_api_calls_with_responses
    ):
        response = handler(event={}, context=context)
        assert response["IsComplete"] is is_active

    assert CheckWorkspaceStatusAPICallBooleans.DescribeWorkspace is True


def test_handler_key_error_fail(context: LambdaContext) -> None:
    def _mock_api_calls_with_responses(
        self: Any, operation_name: str, kwarg: Any
    ) -> Any:
        mocked_response = {
            "DescribeWorkspace": {
                "workspace": {
                    "invalid_key": "ACTIVE",
                },
            },
        }
        return mock_make_api_call(self, operation_name, kwarg, mocked_response)

    with patch(
        "botocore.client.BaseClient._make_api_call", new=_mock_api_calls_with_responses
    ):
        response = handler(event={}, context=context)
        assert response["IsComplete"] is False

    assert CheckWorkspaceStatusAPICallBooleans.DescribeWorkspace is True
