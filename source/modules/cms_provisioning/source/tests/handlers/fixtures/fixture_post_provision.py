# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
from typing import Any, Dict

# Third Party Libraries
import pytest


@pytest.fixture(name="post_provision_event")
def fixture_post_provision_event() -> Dict[str, Any]:
    # There are other fields but they are not important for our tests: https://docs.aws.amazon.com/iot/latest/developerguide/registry-events.html
    vin = os.environ["TEST_VIN"]
    return {
        "operation": "CREATED",
        "thingName": f"Vehicle_{vin}",
        "attributes": {
            "provisioned_by_template": os.environ["PROVISIONING_TEMPLATE_NAME"],
            "vin": vin,
            "certificate_id": os.environ["TEST_CERTIFICATE_ID"],
        },
    }


@pytest.fixture(name="post_provision_event_no_template")
def fixture_post_provision_event_no_template() -> Dict[str, Any]:
    vin = os.environ["TEST_VIN"]
    return {
        "operation": "CREATED",
        "thingName": f"Vehicle_{vin}",
        "attributes": {"vin": vin, "certificate_id": os.environ["TEST_CERTIFICATE_ID"]},
    }


@pytest.fixture(name="post_provision_event_no_attributes")
def fixture_post_provision_event_no_attributes() -> Dict[str, Any]:
    vin = os.environ["TEST_VIN"]
    return {
        "operation": "CREATED",
        "thingName": f"Vehicle_{vin}",
        "attributes": {
            "provisioned_by_template": os.environ["PROVISIONING_TEMPLATE_NAME"],
        },
    }


@pytest.fixture(name="post_provision_event_deleted_event")
def fixture_post_provision_event_deleted_event() -> Dict[str, Any]:
    vin = os.environ["TEST_VIN"]
    return {
        "operation": "DELETED",
        "thingName": f"Vehicle_{vin}",
        "attributes": {
            "provisioned_by_template": os.environ["PROVISIONING_TEMPLATE_NAME"],
            "vin": vin,
            "certificate_id": os.environ["TEST_CERTIFICATE_ID"],
        },
    }
