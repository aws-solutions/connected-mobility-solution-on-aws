# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json
from typing import Any, Dict
from unittest.mock import MagicMock

# Connected Mobility Solution on AWS
from ..main import send_cloud_formation_response


def test_send_cloud_formation_response(
    custom_resource_event: Dict[str, Any], mocker: MagicMock
) -> None:
    mocked_requests: MagicMock = mocker.patch("requests.put")

    input_response = {
        "Status": "SUCCESS",
        "Data": None,
    }
    reason = "test-reason"

    expected_response = json.dumps(
        {
            "Status": input_response["Status"],
            "Reason": reason,
            "PhysicalResourceId": custom_resource_event["LogicalResourceId"],
            "StackId": custom_resource_event["StackId"],
            "RequestId": custom_resource_event["RequestId"],
            "LogicalResourceId": custom_resource_event["LogicalResourceId"],
            "Data": input_response["Data"],
        }
    )
    headers = {"Content-Type": "application/json"}

    send_cloud_formation_response(custom_resource_event, input_response, reason)

    mocked_requests.assert_called_with(
        custom_resource_event["ResponseURL"],
        data=expected_response,
        headers=headers,
        timeout=60,
    )
