# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any, Dict

# Third Party Libraries
import pytest


@pytest.fixture(name="publish_event")
def fixture_publish_lambda_event() -> Dict[str, Any]:
    return {
        "arguments": {
            "vin": "test-vin",
            "alarm_type": "TEST_ALARM",
            "message": "test notification",
        },
        "info": {
            "fieldName": "publish",
        },
    }
