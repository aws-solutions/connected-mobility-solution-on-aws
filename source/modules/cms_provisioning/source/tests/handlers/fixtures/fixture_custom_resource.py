# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import io
import zipfile
from typing import Any, Dict, Generator

# Third Party Libraries
import pytest
from moto import mock_aws
from mypy_boto3_lambda.type_defs import FunctionConfigurationResponseTypeDef

# AWS Libraries
import boto3

# CMS Common Library
from cms_common.enums.custom_resource import CustomResourceRequestType

# Connected Mobility Solution on AWS
from ....handlers.custom_resource.function.lib.custom_resource_type_enum import (
    CustomResourceFunctionType,
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


@pytest.fixture(name="rotate_secret_lambda_function")
def fixture_rotate_secret_lambda_function() -> Generator[
    FunctionConfigurationResponseTypeDef, None, None
]:
    with mock_aws():
        iam_client = boto3.client("iam")
        iam_role = iam_client.create_role(
            RoleName="test-rotate-secret-lambda-role",
            AssumeRolePolicyDocument="test-policy",
            Path="/my-path/",
        )["Role"]["Arn"]

        lambda_client = boto3.client("lambda")

        # Create a valid empty zip file
        zip_file_byte_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_file_byte_buffer, mode="w"):
            pass

        rotate_secret_lambda_function = lambda_client.create_function(
            FunctionName="test-rotate-secret-lambda-arn",
            Role=iam_role,
            Code={"ZipFile": zip_file_byte_buffer.getvalue()},
        )
        yield rotate_secret_lambda_function


@pytest.fixture(name="custom_resource_load_or_create_iot_credentials_event")
def fixture_custom_resource_load_or_create_iot_credentials_event(
    custom_resource_event: Dict[str, Any],
    rotate_secret_lambda_function: FunctionConfigurationResponseTypeDef,
) -> Dict[str, Any]:

    custom_resource_event["RequestType"] = CustomResourceRequestType.CREATE.value
    custom_resource_event["ResourceProperties"] = {
        "Resource": CustomResourceFunctionType.LOAD_OR_CREATE_IOT_CREDENTIALS.value,
        "IoTCredentialsSecretId": "test-credentials-id",
        "RotateSecretLambdaARN": rotate_secret_lambda_function["FunctionArn"],
    }
    return custom_resource_event


@pytest.fixture(name="custom_resource_update_event_configurations_event")
def fixture_custom_resource_update_event_configurations_event(
    custom_resource_event: Dict[str, Any],
) -> Dict[str, Any]:
    custom_resource_event["RequestType"] = CustomResourceRequestType.CREATE.value
    custom_resource_event["ResourceProperties"] = {
        "Resource": CustomResourceFunctionType.UPDATE_EVENT_CONFIGURATIONS.value,
    }
    return custom_resource_event
