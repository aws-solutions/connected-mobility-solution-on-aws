# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any, Dict

# Third Party Libraries
import pytest

# Connected Mobility Solution on AWS
from ..lib.custom_resource_type_enum import CustomResourceFunctionType
from ..main import get_bedrock_agent_client, get_opensearchserverless_client


@pytest.fixture(name="custom_resource_setup")
def fixture_custom_resource_setup() -> Any:
    get_opensearchserverless_client.cache_clear()
    get_bedrock_agent_client.cache_clear()


@pytest.fixture(name="custom_resource_event")
def fixture_custom_resource_event() -> Dict[str, Any]:
    return {
        "ResponseURL": "https://test-response-url.com",
        "StackId": "TestStackId",
        "RequestId": "TestRequestId",
        "ResourceType": "TestResourceType",
        "LogicalResourceId": "TestLogicalResourceId",
        "PhysicalResourceId": "TestPysicalResourceId",
        "ResourceProperties": {},
    }


@pytest.fixture(name="custom_resource_ingest_bedrock_data_source_event")
def fixture_custom_resource_ingest_bedrock_data_source_event(
    custom_resource_event: Dict[str, Any],
) -> Dict[str, Any]:
    custom_resource_event["ResourceProperties"] = {
        "Resource": CustomResourceFunctionType.INGEST_BEDROCK_DATA_SOURCE.value,
        "DataSourceId": "test-data-source-id",
        "KnowledgeBaseId": "test-knowledge-base-id",
    }
    return custom_resource_event
