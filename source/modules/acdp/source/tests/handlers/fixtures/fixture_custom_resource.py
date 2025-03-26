# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any, Callable, Dict, cast

# Third Party Libraries
import pytest
from moto import mock_aws
from mypy_boto3_s3 import S3Client

# AWS Libraries
import boto3
from aws_lambda_powertools.utilities.typing import LambdaContext

# Connected Mobility Solution on AWS
from ....handlers.custom_resource.function.main import CustomResourceTypes


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


@pytest.fixture(name="custom_resource_create_deployment_uuid_event")
def fixture_custom_resource_create_deployment_uuid_event(
    custom_resource_event: Dict[str, Any],
) -> Dict[str, Any]:
    custom_resource_event["RequestType"] = CustomResourceTypes.RequestTypes.CREATE.value
    custom_resource_event["ResourceProperties"][
        "Resource"
    ] = CustomResourceTypes.ResourceTypes.CREATE_DEPLOYMENT_UUID.value

    return custom_resource_event


@pytest.fixture(name="custom_resource_create_and_upload_default_users_and_groups_event")
def fixture_custom_resource_create_and_upload_default_users_and_groups_event(
    custom_resource_event: Dict[str, Any],
) -> Dict[str, Any]:
    custom_resource_event["RequestType"] = CustomResourceTypes.RequestTypes.CREATE.value
    custom_resource_event["ResourceProperties"][
        "Resource"
    ] = (
        CustomResourceTypes.ResourceTypes.CREATE_AND_UPLOAD_DEFAULT_USERS_AND_GROUPS.value
    )
    custom_resource_event["ResourceProperties"]["DestinationBucket"] = "test-bucket"
    custom_resource_event["ResourceProperties"][
        "DestinationKeyPrefix"
    ] = "test-key-prefix"
    custom_resource_event["ResourceProperties"]["CustomEnvironment"] = {
        "ADMIN_USER_EMAIL": "admin",
        "ADMIN_USERNAME": "admin@test.com",
    }

    return custom_resource_event


@pytest.fixture(name="mock_s3_bucket")
def fixture_mock_s3_bucket() -> Callable[[], None]:
    @mock_aws
    def moto_boto() -> None:
        s3_client: S3Client = boto3.client("s3")
        s3_client.create_bucket(Bucket="test-bucket")

    return moto_boto


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
