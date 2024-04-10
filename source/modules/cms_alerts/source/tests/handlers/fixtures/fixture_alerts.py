# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json
from typing import Any, Dict

# Third Party Libraries
import pytest


@pytest.fixture(name="alerts_event")
def fixture_alerts_lambda_event() -> Dict[str, Any]:
    return {
        "Records": [
            {
                "messageId": "test-msg-id",
                "receiptHandle": "test-receipt-handle",
                "body": json.dumps(
                    {
                        "Message": json.dumps(
                            {
                                "vin": "test-vin",
                                "alarm_type": "TEST_ALARM",
                                "message": "test notification",
                            }
                        )
                    }
                ),
                "attributes": {
                    "ApproximateReceiveCount": "1",
                    "SentTimestamp": "1523232000000",
                    "SenderId": "123456789012",
                    "ApproximateFirstReceiveTimestamp": "1523232000001",
                },
                "messageAttributes": {},
                "md5OfBody": "test-md5-of-body",
                "eventSource": "aws:sqs",
                "eventSourceARN": "0000000000000000000000000000000000:test-queue",
                "awsRegion": "us-east-1",
            },
        ]
    }
