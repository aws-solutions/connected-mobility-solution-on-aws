# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
from typing import Any, Dict

# Third Party Libraries
import pytest


@pytest.fixture(name="initial_connection_event_valid")
def fixture_initial_connection_event_valid() -> Dict[str, Any]:
    return {
        "vin": os.environ["TEST_VIN"],
        "certificate_id": os.environ["TEST_CERTIFICATE_ID"],
    }


@pytest.fixture(name="initial_connection_event_invalid")
def fixture_initial_connection_event_invalid() -> Dict[str, Any]:
    return {
        "vin": os.environ["TEST_VIN"],
    }
