# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any, Dict

# Third Party Libraries
import pytest


@pytest.fixture(name="notifications_event")
def fixture_notifications_lambda_event() -> Dict[str, Any]:
    return {
        "Records": [
            {
                "dynamodb": {
                    "NewImage": {
                        "topic": {"S": "test-topic"},
                        "message": {"S": "test notification"},
                    },
                    "Keys": {"TestKey": {"S": "TestValue"}},
                    "SequenceNumber": "123",
                    "SizeBytes": 1,
                    "StreamViewType": "TestStreamType",
                },
                "eventName": "TestEvent",
                "eventSource": "TestArn",
                "awsRegion": "us-east-1",
                "eventId": "123",
                "eventVersion": "1",
                "userIdentity": None,
                "eventSourceARN": None,
            }
        ]
    }
