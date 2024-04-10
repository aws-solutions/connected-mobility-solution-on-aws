# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any, Dict, Generator

# Third Party Libraries
import pytest
from moto import mock_aws

# AWS Libraries
import boto3

# CMS Common Library
from cms_common.enums.aws_resource_lookup import AwsResourceLookupCustomResourceType
from cms_common.enums.custom_resource import CustomResourceRequestType
from cms_common.resource_names.config import ConfigResourceNames

TEST_APP_UNIQUE_ID = "test-app"
TEST_IDENTITY_PROVIDER_ID = "test-idp"
TEST_CONFIG_RESOURCE_NAMES_CLASS = ConfigResourceNames.from_app_unique_id(
    TEST_APP_UNIQUE_ID
)


@pytest.fixture(name="aws_resource_lookup_event", scope="module")
def fixture_aws_resource_lookup_event() -> Dict[str, Any]:
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


@pytest.fixture(name="aws_resource_lookup_event_identity_provider_id", scope="module")
def fixture_aws_resource_lookup_event_identity_provider_id(
    aws_resource_lookup_event: Dict[str, Any],
) -> Dict[str, Any]:
    aws_resource_lookup_event["RequestType"] = CustomResourceRequestType.CREATE.value
    aws_resource_lookup_event["ResourceProperties"][
        "Resource"
    ] = AwsResourceLookupCustomResourceType.SSM_PARAMETERS.value
    aws_resource_lookup_event["ResourceProperties"][
        "ParameterName"
    ] = TEST_CONFIG_RESOURCE_NAMES_CLASS.identity_provider_id_ssm_parameter

    return aws_resource_lookup_event


@pytest.fixture(name="mock_boto_identity_provider_id_ssm_parameter")
def fixture_mock_boto_identity_provider_id_ssm_parameter() -> Generator[
    None, None, None
]:
    with mock_aws():
        ssm_client = boto3.client("ssm")
        ssm_client.put_parameter(
            Name=TEST_CONFIG_RESOURCE_NAMES_CLASS.identity_provider_id_ssm_parameter,
            Value=TEST_IDENTITY_PROVIDER_ID,
            Type="String",
        )
        yield
