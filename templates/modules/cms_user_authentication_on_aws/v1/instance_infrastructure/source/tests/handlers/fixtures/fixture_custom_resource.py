# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any, Dict, Generator

# Third Party Libraries
import boto3
import pytest
from moto import mock_cognitoidp  # type: ignore

# Connected Mobility Solution on AWS
from ....handlers.custom_resource.lib.custom_resource_type_enum import (
    CustomResourceType,
)


@pytest.fixture(name="custom_resource_event")
def fixture_custom_resource_event() -> Dict[str, Any]:
    return {
        "ResponseURL": "https://test-response-url.com",
        "StackId": "test-stack-id",
        "RequestId": "test-request-id",
        "ResourceType": "test-resource-type",
        "LogicalResourceId": "test-logical-resource-id",
        "PhysicalResourceId": "test-physical-resource-id",
        "OldResourceProperties": {},
    }


@pytest.fixture(name="custom_resource_manage_user_pool_domain_event")
def fixture_custom_resource_manage_user_pool_domain_event(
    custom_resource_event: Dict[str, Any],
) -> Generator[Dict[str, Any], None, None]:
    with mock_cognitoidp():
        cognito_client = boto3.client("cognito-idp")
        user_pool = cognito_client.create_user_pool(
            PoolName="test-user-pool-cms-authentication"
        )
        custom_resource_event[
            "RequestType"
        ] = CustomResourceType.RequestType.CREATE.value
        custom_resource_event["ResourceProperties"] = {
            "Resource": CustomResourceType.ResourceType.MANAGE_USER_POOL_DOMAIN.value,
            "UserPoolId": user_pool["UserPool"]["Id"],
        }
        yield custom_resource_event
