# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0


# Standard Library
# mypy: disable-error-code=misc
import json
from typing import Any, Dict
from unittest.mock import MagicMock

# Third Party Libraries
import boto3
from aws_lambda_powertools.utilities.typing import LambdaContext
from moto import mock_cognitoidp, mock_s3  # type: ignore

# Connected Mobility Solution on AWS
from ....handlers.custom_resource import custom_resource


def test_handler(
    custom_resource_create_event: Dict[str, Any],
    context: LambdaContext,
    mocker: MagicMock,
) -> None:
    mocked_requests: MagicMock = mocker.patch("requests.put")

    custom_resource_create_event["ResourceProperties"]["Resource"] = "CreateUUID"
    custom_resource_create_event["ResourceProperties"]["StackName"] = "TestStack"

    response = custom_resource.handler(custom_resource_create_event, context)

    mocked_requests.assert_called_once()
    data: Dict[str, Any] = response["Data"]
    assert data.keys() == {"UUID", "UNIQUE_SUFFIX", "REDUCED_STACK_NAME"}


def test_create_uuid(custom_resource_create_event: Dict[str, Any]) -> None:
    custom_resource_create_event = {"ResourceProperties": {"StackName": "test-stack"}}
    response = custom_resource.create_uuid(custom_resource_create_event)

    assert response["UUID"]
    assert "-" not in response["UNIQUE_SUFFIX"]
    assert len(response["REDUCED_STACK_NAME"]) <= 10


def test_send_cloud_formation_response(
    custom_resource_create_event: Dict[str, Any], mocker: MagicMock
) -> None:
    mocked_requests: MagicMock = mocker.patch("requests.put")

    custom_resource_create_event = {
        "LogicalResourceId": "TestResourceId",
        "RequestId": "TestRequestId",
        "StackId": "TestStackId",
        "ResponseURL": "TestResponseURL",
    }
    input_response = {
        "Status": "SUCCESS",
        "Data": None,
    }
    reason = "TestReason"

    expected_response = json.dumps(
        {
            "Status": input_response["Status"],
            "Reason": reason,
            "PhysicalResourceId": custom_resource_create_event["LogicalResourceId"],
            "StackId": custom_resource_create_event["StackId"],
            "RequestId": custom_resource_create_event["RequestId"],
            "LogicalResourceId": custom_resource_create_event["LogicalResourceId"],
            "Data": input_response["Data"],
        }
    )
    headers = {"Content-Type": "application/json"}

    custom_resource.send_cloud_formation_response(
        custom_resource_create_event, input_response, reason
    )

    mocked_requests.assert_called_with(
        custom_resource_create_event["ResponseURL"],
        data=expected_response,
        headers=headers,
        timeout=60,
    )


@mock_s3
def test_create_console_config(custom_resource_create_event: Dict[str, Any]) -> None:
    destination_bucket = "TestDestinationBucket"
    config_file_name = "TestConfigFileName"
    config_obj = '{"test": "test"}'
    custom_resource_create_event["ResourceProperties"] = {
        "DestinationBucket": destination_bucket,
        "ConfigFileName": config_file_name,
        "configObj": config_obj,
    }

    # Specifying region is necessary for the create_bucket moto call
    s3_client = boto3.client("s3", region_name="us-east-1")
    s3_resource = boto3.resource("s3", region_name="us-east-1")

    s3_client.create_bucket(Bucket=destination_bucket)
    response = custom_resource.create_console_config(custom_resource_create_event)

    assert response["Bucket"] == destination_bucket

    body = (
        s3_resource.Object(destination_bucket, config_file_name)
        .get()["Body"]
        .read()
        .decode("utf-8")
    )

    set_config, config_value = body.split(" = ")
    assert set_config == "const config"
    assert json.dumps(config_value[:-1])  # Remove the semicolon at the end


def test_detach_iot_policy(
    mocker: MagicMock, custom_resource_delete_event: Dict[str, Any]
) -> None:
    test_targets = {"targets": ["test1", "test2"]}
    # moto does not support the service calls used in this method
    mocked_iot: MagicMock = mocker.patch(
        "botocore.client.BaseClient._make_api_call",
        return_value=test_targets,
    )

    policy_name = "TestIOTPolicy"
    custom_resource_delete_event["ResourceProperties"] = {"IoTPolicyName": policy_name}

    custom_resource.detach_iot_policy(custom_resource_delete_event)

    # +1 Extra call to list policy targets
    assert mocked_iot.call_count == len(test_targets["targets"]) + 1


@mock_cognitoidp
def test_create_userpool_user(custom_resource_create_event: Dict[str, Any]) -> None:
    cognito = boto3.client("cognito-idp")
    user_pool = cognito.create_user_pool(PoolName="TestUserPool")
    test_username = "TestUser"

    custom_resource_create_event["ResourceProperties"].update(
        {
            "UserpoolId": user_pool["UserPool"]["Id"],
            "Username": test_username,
            "UserAttributes": [],
            "DesiredDeliveryMediums": ["EMAIL"],
            "ForceAliasCreation": True,
        }
    )

    custom_resource.create_userpool_user(custom_resource_create_event)
    users = cognito.list_users(UserPoolId=user_pool["UserPool"]["Id"])["Users"]
    assert users[0]["Username"] == test_username
