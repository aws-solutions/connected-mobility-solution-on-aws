# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any, Dict, cast

# Third Party Libraries
import pytest
from aws_lambda_powertools.utilities.typing import LambdaContext

# Connected Mobility Solution on AWS
from ....infrastructure.handlers.custom_resource import custom_resource


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
        "OldResourceProperties": {},
    }


@pytest.fixture(name="custom_resource_create_event")
def fixture_custom_resource_create_event(
    custom_resource_event: Dict[str, Any],
) -> Dict[str, Any]:
    custom_resource_event[
        "RequestType"
    ] = custom_resource.CustomResourceTypes.RequestTypes.CREATE.value
    custom_resource_event["ResourceProperties"]["Resource"] = "CreateProtonEnvironment"
    custom_resource_event["ResourceProperties"]["StackName"] = "CmsTestStack"
    custom_resource_event["ResourceProperties"][
        "TEMPLATE_S3_BUCKET_NAME"
    ] = "CmsTestTemplateBucket"
    custom_resource_event["ResourceProperties"][
        "TEMPLATE_S3_KEY_PREFIX"
    ] = "test-key-prefix/"
    custom_resource_event["ResourceProperties"][
        "CODE_BUILD_IAM_ROLE"
    ] = "arn:aws:iam::1234567890:role/cms-test-build-role"

    return custom_resource_event


@pytest.fixture(name="custom_resource_create_deployment_uuid_event")
def fixture_custom_resource_create_deployment_uuid_event(
    custom_resource_event: Dict[str, Any],
) -> Dict[str, Any]:
    custom_resource_event[
        "RequestType"
    ] = custom_resource.CustomResourceTypes.RequestTypes.CREATE.value
    custom_resource_event["ResourceProperties"]["Resource"] = "CreateDeploymentUUID"

    return custom_resource_event


@pytest.fixture(name="context")
def fixture_context() -> LambdaContext:
    class MockLambdaContext:
        def __init__(self) -> None:
            self.function_name = "test"
            self.memory_limit_in_mb = 128
            self.invoked_function_arn = (
                "arn:aws:lambda:eu-west-1:809313241:function:test"
            )
            self.aws_request_id = "52fdfc07-2182-154f-163f-5f0f9a621d72"
            self.log_stream_name = "TestLogSteam"

        def get_remaining_time_in_millis(self) -> int:
            # This is hardcoded to allow the custom_resource handler to execute. It must be greater than the REMAINING_TIME_THRESHOLD for execution to be successful.
            return 60000

    return cast(LambdaContext, MockLambdaContext())
