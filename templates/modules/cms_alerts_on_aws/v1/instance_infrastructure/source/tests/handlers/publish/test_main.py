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
from ....handlers.publish import main


def test_publish_handler_success(
    publish_event: Dict[str, Any], context: LambdaContext, mocker: mock.MagicMock
) -> None:
    mocker.patch("botocore.client.BaseClient._make_api_call", return_value={})
    response = main.handler(publish_event, context)

    assert response["status"] == "SUCCESS"


def test_publish_handler_failure(
    publish_event: Dict[str, Any], context: LambdaContext, mocker: mock.MagicMock
) -> None:
    mocker.patch(
        "botocore.client.BaseClient._make_api_call",
        side_effect=botocore.exceptions.ClientError(
            error_response={"Error": {"Code": "test", "Message": "test"}},
            operation_name="publish",
        ),
    )
    response = main.handler(publish_event, context)

    assert response["status"] == "FAILURE"
    assert (
        response["message"]
        == "Error occured while publishing the message: {'vin': 'test-vin', 'alarm_type': 'TEST_ALARM', 'message': 'test notification'}"  # pylint: disable=line-too-long
    )
