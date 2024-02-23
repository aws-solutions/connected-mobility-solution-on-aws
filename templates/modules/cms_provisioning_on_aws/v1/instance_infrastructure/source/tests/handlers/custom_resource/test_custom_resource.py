# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0


# Standard Library
# mypy: disable-error-code=misc
import json
import uuid
from typing import Any, Dict
from unittest.mock import MagicMock, patch

# Third Party Libraries
import boto3
import botocore
import pytest
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.exceptions import ClientError
from moto import mock_aws  # type: ignore[import-untyped]

# Connected Mobility Solution on AWS
from ....handlers.custom_resource.custom_resource import (
    handler,
    load_or_create_iot_credentials,
    send_cloud_formation_response,
    update_event_configurations,
)
from ....handlers.custom_resource.lib.custom_resource_type_enum import (
    CustomResourceType,
)


# Flags to assert that an API call happened
class CustomResourceAPICallBooleans:
    UpdateEventConfigurations = False

    @classmethod
    def reset_values(cls) -> None:
        for var in vars(CustomResourceAPICallBooleans):
            if not callable(
                getattr(CustomResourceAPICallBooleans, var)
            ) and not var.startswith("__"):
                setattr(CustomResourceAPICallBooleans, var, False)

    @classmethod
    def are_all_values_false(cls) -> bool:
        are_all_values_false = True
        for var in vars(CustomResourceAPICallBooleans):
            if not callable(
                getattr(CustomResourceAPICallBooleans, var)
            ) and not var.startswith("__"):
                if getattr(CustomResourceAPICallBooleans, var):
                    are_all_values_false = False
                    break
        return are_all_values_false


# pylint: disable=protected-access
orig = botocore.client.BaseClient._make_api_call  # type: ignore


# pylint: disable=too-many-return-statements, inconsistent-return-statements
def mock_make_api_call(self: Any, operation_name: str, kwarg: Any) -> Any:
    setattr(CustomResourceAPICallBooleans, operation_name, True)
    mock_api_responses = {"UpdateEventConfigurations": None}
    if operation_name in mock_api_responses:
        return mock_api_responses[operation_name]
    return orig(self, operation_name, kwarg)


@mock_aws
def test_handler(
    custom_resource_load_or_create_iot_credentials_event: Dict[str, Any],
    context: LambdaContext,
    mocker: MagicMock,
) -> None:
    mocked_requests: MagicMock = mocker.patch("requests.put")
    with patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call):
        response = handler(
            custom_resource_load_or_create_iot_credentials_event, context
        )
    mocked_requests.assert_called_once()
    data: Dict[str, Any] = response["Data"]

    assert data.keys() == {"CERTIFICATE_PEM"}
    assert response["Status"] == CustomResourceType.StatusType.SUCCESS.value


def test_handler_invalid_event(
    custom_resource_event: Dict[str, Any],
    context: LambdaContext,
    mocker: MagicMock,
) -> None:
    mocked_requests: MagicMock = mocker.patch("requests.put")
    response = handler(custom_resource_event, context)
    mocked_requests.assert_called_once()

    assert response["Status"] == CustomResourceType.StatusType.FAILED.value


def test_update_event_configurations(
    custom_resource_update_event_configurations_event: Dict[str, Any],
) -> None:
    assert CustomResourceAPICallBooleans.are_all_values_false()
    with patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call):
        update_event_configurations(custom_resource_update_event_configurations_event)
    assert CustomResourceAPICallBooleans.UpdateEventConfigurations is True


def test_send_cloud_formation_response(
    custom_resource_event: Dict[str, Any], mocker: MagicMock
) -> None:
    mocked_requests: MagicMock = mocker.patch("requests.put")

    input_response = {
        "Status": "SUCCESS",
        "Data": None,
    }
    reason = "test-reason"

    expected_response = json.dumps(
        {
            "Status": input_response["Status"],
            "Reason": reason,
            "PhysicalResourceId": custom_resource_event["LogicalResourceId"],
            "StackId": custom_resource_event["StackId"],
            "RequestId": custom_resource_event["RequestId"],
            "LogicalResourceId": custom_resource_event["LogicalResourceId"],
            "Data": input_response["Data"],
        }
    )
    headers = {"Content-Type": "application/json"}

    send_cloud_formation_response(custom_resource_event, input_response, reason)

    mocked_requests.assert_called_with(
        custom_resource_event["ResponseURL"],
        data=expected_response,
        headers=headers,
        timeout=60,
    )


@mock_aws
def test_create_iot_credentials(
    custom_resource_load_or_create_iot_credentials_event: Dict[str, Any]
) -> None:
    test_credentials_id = custom_resource_load_or_create_iot_credentials_event[
        "ResourceProperties"
    ]["IoTCredentialsSecretId"]

    secrets_manager_client = boto3.client("secretsmanager")

    # assert that secret does not exist
    with pytest.raises(ClientError):
        secrets_manager_client.get_secret_value(SecretId=test_credentials_id)

    load_or_create_iot_credentials(
        event=custom_resource_load_or_create_iot_credentials_event
    )

    # assert that secret was created
    secret = json.loads(
        secrets_manager_client.get_secret_value(SecretId=test_credentials_id)[
            "SecretString"
        ]
    )

    assert secret["certificatePem"]
    assert secret["keyPair"]["PrivateKey"]
    assert secret["keyPair"]["PublicKey"]


@mock_aws
def test_load_iot_credentials(
    custom_resource_load_or_create_iot_credentials_event: Dict[str, Any]
) -> None:
    test_credentials_id = custom_resource_load_or_create_iot_credentials_event[
        "ResourceProperties"
    ]["IoTCredentialsSecretId"]

    secrets_manager_client = boto3.client("secretsmanager")
    iot_client = boto3.client("iot")

    # create secret beforehand
    iot_credentials = iot_client.create_keys_and_certificate(setAsActive=False)
    secrets_manager_client.create_secret(
        Name=test_credentials_id,
        ClientRequestToken=str(uuid.uuid4()),
        Description="IoT certificate and key pair to be used when provisioning vehicle.",
        SecretString=json.dumps(iot_credentials),
    )

    load_or_create_iot_credentials(
        event=custom_resource_load_or_create_iot_credentials_event
    )

    # assert that existing secret was loaded instead of creating a new secret
    secret = secrets_manager_client.get_secret_value(SecretId=test_credentials_id)
    assert json.loads(secret["SecretString"]) == iot_credentials
