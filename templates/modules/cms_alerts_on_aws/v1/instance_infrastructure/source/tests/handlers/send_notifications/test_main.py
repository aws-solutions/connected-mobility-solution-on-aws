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
from ....handlers.send_notifications import main


def test_notifications_handler_success(
    notifications_event: Dict[str, Any], context: LambdaContext, mocker: mock.MagicMock
) -> None:
    mock_obj = mocker.patch(
        "botocore.client.BaseClient._make_api_call",
        return_value={
            "TopicArn": "test-topic-arn",
            "MessageId": "test-message-id",
            "SequenceNumber": "test-sequence-number",
        },
    )

    # Nothing to return just checking if function executes without errors
    main.handler(notifications_event, context)

    mock_obj.assert_called()


def test_notifications_handler_failure(
    notifications_event: Dict[str, Any], context: LambdaContext, mocker: mock.MagicMock
) -> None:
    mocker.patch(
        "botocore.client.BaseClient._make_api_call",
        side_effect=botocore.exceptions.ClientError(
            error_response={"Error": {"Code": "test", "Message": "test"}},
            operation_name="publish",
        ),
    )

    with mock.patch("botocore.client.BaseClient._make_api_call") as mock_logger:
        try:
            main.handler(notifications_event, context)
        except botocore.exceptions.ClientError:
            mock_logger.assert_called_with(
                "Error encountered while publishing notification test"
            )
