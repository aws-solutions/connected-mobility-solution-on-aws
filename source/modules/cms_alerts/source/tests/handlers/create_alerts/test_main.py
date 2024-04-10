# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
# mypy: disable-error-code=misc
from typing import Any, Dict
from unittest import mock

# AWS Libraries
import botocore
from aws_lambda_powertools.utilities.typing import LambdaContext

# Connected Mobility Solution on AWS
from ....handlers.create_alerts.app import main


def test_alerts_handler_success(
    alerts_event: Dict[str, Any], context: LambdaContext, mocker: mock.MagicMock
) -> None:
    mocker.patch("botocore.client.BaseClient._make_api_call", return_value={})

    main.handler(alerts_event, context)


def test_alerts_handler_failure(
    alerts_event: Dict[str, Any], context: LambdaContext, mocker: mock.MagicMock
) -> None:
    mocker.patch(
        "botocore.client.BaseClient._make_api_call",
        side_effect=botocore.exceptions.ClientError(
            error_response={"Error": {"Code": "test", "Message": "test"}},
            operation_name="put_item",
        ),
    )

    with mock.patch("botocore.client.BaseClient._make_api_call") as mock_logger:
        try:
            main.handler(alerts_event, context)
        except botocore.exceptions.ClientError:
            mock_logger.assert_called_with(
                "Error encountered while processing message test"
            )
