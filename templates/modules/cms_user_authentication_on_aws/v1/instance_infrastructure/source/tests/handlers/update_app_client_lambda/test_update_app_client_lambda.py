# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
# mypy: disable-error-code=misc
from typing import Any, Dict
from unittest import mock

# Third Party Libraries
import botocore
from aws_lambda_powertools.utilities.typing import LambdaContext

# Connected Mobility Solution on AWS
from ....handlers.update_app_client_lambda import main


def test_update_app_client_lambda_success(
    update_app_client_lambda_event: Dict[str, Any],
    context: LambdaContext,
    mocker: mock.MagicMock,
) -> None:
    mocker.patch(
        "botocore.client.BaseClient._make_api_call",
        return_value={
            "UserPoolClient": {"ClientId": "TestAppClientId"},
        },
    )

    response = main.handler(update_app_client_lambda_event, context)

    assert response["Data"]["ClientId"] == "TestAppClientId"
    assert response["Status"] == "SUCCESS"


def test_update_app_client_lambda_fail(
    update_app_client_lambda_event: Dict[str, Any],
    context: LambdaContext,
    mocker: mock.MagicMock,
) -> None:
    mocker.patch(
        "botocore.client.BaseClient._make_api_call",
        side_effect=botocore.exceptions.ParamValidationError(report="test error"),
    )

    response = main.handler(update_app_client_lambda_event, context)

    assert response["Status"] == "FAILED"
    assert response["ErrorMessage"] == "parameter validation failed"
