# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any, Dict

# Third Party Libraries
import pytest

# CMS Common Library
from cms_common.enums.custom_resource import CustomResourceRequestType


@pytest.fixture(name="custom_resource_event", scope="module")
def fixture_custom_resource_event() -> Dict[str, Any]:
    return {
        "ResponseURL": "https://test-response-url.com",
        "StackId": "TestStackId",
        "RequestId": "TestRequestId",
        "ResourceType": "TestResourceType",
        "LogicalResourceId": "TestLogicalResourceId",
        "PhysicalResourceId": "TestPysicalResourceId",
        "ResourceProperties": {},
        "OldResourceProperties": {},
    }


@pytest.fixture(name="custom_resource_create_deployment_uuid_event", scope="module")
def fixture_custom_resource_create_deployment_uuid_event(
    custom_resource_event: Dict[str, Any],
) -> Dict[str, Any]:
    custom_resource_event["RequestType"] = CustomResourceRequestType.CREATE.value
    custom_resource_event["ResourceProperties"]["Resource"] = "CreateDeploymentUUID"

    return custom_resource_event
