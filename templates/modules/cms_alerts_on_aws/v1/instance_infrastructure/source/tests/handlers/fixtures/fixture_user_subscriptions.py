# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any, Dict

# Third Party Libraries
import pytest


@pytest.fixture(name="user_subscriptions_get_event")
def fixture_user_subscriptions_get_lambda_event() -> Dict[str, Any]:
    return {"arguments": {"email": "test-email"}}


@pytest.fixture(name="user_subscriptions_create_event")
def fixture_user_subscriptions_create_lambda_event() -> Dict[str, Any]:
    return {"arguments": {"email": "test-email", "vins": ["1", "2"]}}


@pytest.fixture(name="user_subscriptions_update_event")
def fixture_user_subscriptions_update_lambda_event() -> Dict[str, Any]:
    return {
        "arguments": {
            "email": "test-email",
            "alarms": [
                {
                    "vin": "test-vin",
                    "alarm_type": "test-alarm-type",
                    "email_enabled": True,
                },
                {
                    "vin": "test-vin1",
                    "alarm_type": "test-alarm-type1",
                    "email_enabled": True,
                },
            ],
        }
    }


@pytest.fixture(name="user_subscriptions_handler_event")
def fixture_user_subscriptions_handler_lambda_event() -> Dict[str, Any]:
    return {
        "arguments": {"email": "test-email"},
        "info": {"fieldName": "getUserSubscriptions"},
    }
