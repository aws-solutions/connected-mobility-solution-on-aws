# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any, Dict

# Third Party Libraries
import pytest


@pytest.fixture(name="simulate_data_event")
def fixture_simulate_data_event() -> Dict[str, Any]:
    return {
        "simulation": {
            "interval": 1,
            "duration": 5,
        },
        "options": {},
        "info": {
            "payload": {"L": [{"M": {"name": {"S": "test"}, "type": {"S": "id"}}}]},
            "topic": {"S": "test"},
            "name": {
                "S": "test_device",
            },
        },
        "index": 0,
    }


@pytest.fixture(name="limits")
def fixture_limits() -> Dict[str, Any]:
    return {
        "min": 1,
        "max": 100,
        "precision": 5,
        "lat": 50.0,
        "long": 50.0,
        "payload": [
            {
                "name": "test_id",
                "type": "id",
            },
            {
                "name": "test_bool",
                "type": "bool",
            },
        ],
        "arr": [1, 2, 3],
    }
