# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0


# Standard Library
# mypy: disable-error-code=misc
import json
from typing import Any, Dict
from unittest.mock import patch

# Third Party Libraries
import pytest

# AWS Libraries
import boto3
import botocore
from aws_lambda_powertools.utilities.typing import LambdaContext

# Connected Mobility Solution on AWS
from ....handlers.rotate_secret.function.lib.custom_exceptions import (
    GrafanaApiError,
    InvalidSecretRotationStepError,
    SecretRotationNotEnabledError,
    SecretRotationNotStagedError,
)
from ....handlers.rotate_secret.function.lib.rotate_secret_enum import (
    RotateSecretStep,
    SecretStatus,
)
from ....handlers.rotate_secret.function.main import handler


class RotateSecretAPICallBooleans:
    CreateWorkspaceApiKey = False
    DeleteWorkspaceApiKey = False

    @classmethod
    def reset_values(cls) -> None:
        for var in vars(RotateSecretAPICallBooleans):
            if not callable(
                getattr(RotateSecretAPICallBooleans, var)
            ) and not var.startswith("__"):
                setattr(RotateSecretAPICallBooleans, var, False)

    @classmethod
    def are_all_values_false(cls) -> bool:
        are_all_values_false = True
        for var in vars(RotateSecretAPICallBooleans):
            if not callable(
                getattr(RotateSecretAPICallBooleans, var)
            ) and not var.startswith("__"):
                if getattr(RotateSecretAPICallBooleans, var):
                    are_all_values_false = False
                    break
        return are_all_values_false


# pylint: disable=protected-access
orig = botocore.client.BaseClient._make_api_call  # type: ignore
# pylint: disable=too-many-return-statements, inconsistent-return-statements
def mock_make_api_call(self: Any, operation_name: str, kwarg: Any) -> Any:
    setattr(RotateSecretAPICallBooleans, operation_name, True)
    mock_api_responses = {
        "CreateWorkspaceApiKey": {
            "key": "test-grafana-api-key",
            "workspaceId": "test-grafana-workspace-id",
        },
        "DeleteWorkspaceApiKey": None,
    }
    if operation_name in mock_api_responses:
        return mock_api_responses[operation_name]
    return orig(self, operation_name, kwarg)


@pytest.mark.parametrize("missing_key", ["SecretId", "ClientRequestToken", "Step"])
def test_handler_missing_key_from_event(
    missing_key: str, rotate_secret_event_valid: Dict[str, Any], context: LambdaContext
) -> None:
    rotate_secret_event_valid.pop(missing_key)
    with pytest.raises(KeyError):
        handler(rotate_secret_event_valid, context)


def test_handler_rotation_not_enabled(
    rotate_secret_event_rotation_not_enabled: Dict[str, Any],
    context: LambdaContext,
) -> None:
    with pytest.raises(SecretRotationNotEnabledError):
        handler(rotate_secret_event_rotation_not_enabled, context)


def test_handler_invalid_version_to_stage(
    rotate_secret_event_invalid_version_to_stage: Dict[str, Any],
    context: LambdaContext,
) -> None:
    with pytest.raises(SecretRotationNotStagedError):
        handler(rotate_secret_event_invalid_version_to_stage, context)


def test_handler_invalid_step(
    rotate_secret_event_invalid_step: Dict[str, Any],
    context: LambdaContext,
) -> None:
    with pytest.raises(InvalidSecretRotationStepError):
        handler(rotate_secret_event_invalid_step, context)


def test_handler_create_secret_step_succeeds(
    rotate_secret_event_valid: Dict[str, Any], context: LambdaContext
) -> None:
    # Set the secret rotation step to create secret
    rotate_secret_event_valid["Step"] = RotateSecretStep.CREATE_SECRET.value
    # Call the lambda function
    with patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call):
        handler(rotate_secret_event_valid, context)

    # The create secret step should have put a new iot credentials in the pending secret version
    secretsmanager_client = boto3.client("secretsmanager")
    pending_secret_string = secretsmanager_client.get_secret_value(
        SecretId=rotate_secret_event_valid["SecretId"]
    )["SecretString"]

    # Assert that the secret was appropriately created
    pending_secret_dict = json.loads(pending_secret_string)
    assert isinstance(pending_secret_dict["key"], str)
    assert isinstance(pending_secret_dict["workspaceId"], str)


def test_handler_create_secret_step_secret_already_exists(
    rotate_secret_event_valid: Dict[str, Any], context: LambdaContext
) -> None:
    # Set the secret rotation step to create secret
    rotate_secret_event_valid["Step"] = RotateSecretStep.CREATE_SECRET.value

    # Put a secret in the pending version
    secretsmanager_client = boto3.client("secretsmanager")
    secret_value = "dummy"
    secretsmanager_client.put_secret_value(
        SecretId=rotate_secret_event_valid["SecretId"],
        ClientRequestToken=rotate_secret_event_valid["ClientRequestToken"],
        SecretString=secret_value,
    )

    # Call the lambda function
    with patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call):
        handler(rotate_secret_event_valid, context)

    # Since there was already a secret value in the pending version,
    # the value should be unchanged after calling the create secret step
    assert (
        secret_value
        == secretsmanager_client.get_secret_value(
            SecretId=rotate_secret_event_valid["SecretId"],
            VersionId=rotate_secret_event_valid["ClientRequestToken"],
        )["SecretString"]
    )


def test_handler_set_secret_step_succeeds(
    rotate_secret_event_valid: Dict[str, Any], context: LambdaContext
) -> None:
    # Set the secret rotation step to create secret
    rotate_secret_event_valid["Step"] = RotateSecretStep.CREATE_SECRET.value
    # Call the lambda function
    with patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call):
        handler(rotate_secret_event_valid, context)

    # Set the secret rotation step to set secret
    rotate_secret_event_valid["Step"] = RotateSecretStep.SET_SECRET.value
    # Call the lambda function
    with patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call):
        handler(rotate_secret_event_valid, context)

    # The set secret step should have attached all the policies attached to the current
    # secret's certificate to the pending secret's certificate
    secretsmanager_client = boto3.client("secretsmanager")
    current_api_key = json.loads(
        secretsmanager_client.get_secret_value(
            SecretId=rotate_secret_event_valid["SecretId"],
            VersionStage=SecretStatus.CURRENT.value,
        )["SecretString"]
    )["key"]

    pending_api_key = json.loads(
        secretsmanager_client.get_secret_value(
            SecretId=rotate_secret_event_valid["SecretId"],
            VersionStage=SecretStatus.PENDING.value,
            VersionId=rotate_secret_event_valid["ClientRequestToken"],
        )["SecretString"]
    )["key"]

    assert isinstance(current_api_key, str)
    assert isinstance(pending_api_key, str)


def test_handler_test_secret_step_succeeds(
    rotate_secret_event_valid: Dict[str, Any],
    context: LambdaContext,
) -> None:
    # Set the secret rotation step to create secret
    rotate_secret_event_valid["Step"] = RotateSecretStep.CREATE_SECRET.value
    # Call the lambda function
    with patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call):
        handler(rotate_secret_event_valid, context)

    # Set the secret rotation step to set secret
    rotate_secret_event_valid["Step"] = RotateSecretStep.SET_SECRET.value
    # Call the lambda function
    with patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call):
        handler(rotate_secret_event_valid, context)

    # Set the secret rotation step to test secret
    rotate_secret_event_valid["Step"] = RotateSecretStep.TEST_SECRET.value
    # Call the lambda function
    with patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call):
        with patch("requests.get") as mocked_request_get:
            mocked_request_get.return_value.ok = True
            handler(rotate_secret_event_valid, context)


def test_handler_test_secret_step_fails(
    rotate_secret_event_valid: Dict[str, Any],
    context: LambdaContext,
) -> None:
    # Set the secret rotation step to create secret
    rotate_secret_event_valid["Step"] = RotateSecretStep.CREATE_SECRET.value
    # Call the lambda function
    with patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call):
        handler(rotate_secret_event_valid, context)

    # Set the secret rotation step to set secret
    rotate_secret_event_valid["Step"] = RotateSecretStep.SET_SECRET.value
    # Call the lambda function
    with patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call):
        handler(rotate_secret_event_valid, context)

    # Set the secret rotation step to test secret
    rotate_secret_event_valid["Step"] = RotateSecretStep.TEST_SECRET.value
    # Call the lambda function
    with patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call):
        with patch("requests.get") as mocked_request_get:
            mocked_request_get.return_value.ok = False

            with pytest.raises(GrafanaApiError):
                handler(rotate_secret_event_valid, context)


def test_handler_finish_secret_step_succeeds(
    rotate_secret_event_valid: Dict[str, Any],
    context: LambdaContext,
) -> None:
    # Set the secret rotation step to create secret
    rotate_secret_event_valid["Step"] = RotateSecretStep.CREATE_SECRET.value
    # Call the lambda function
    with patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call):
        handler(rotate_secret_event_valid, context)

    # Set the secret rotation step to set secret
    rotate_secret_event_valid["Step"] = RotateSecretStep.SET_SECRET.value
    # Call the lambda function
    with patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call):
        handler(rotate_secret_event_valid, context)

    # Set the secret rotation step to test secret
    rotate_secret_event_valid["Step"] = RotateSecretStep.TEST_SECRET.value
    # Call the lambda function
    with patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call):
        with patch("requests.get") as mocked_request_get:
            mocked_request_get.return_value.ok = True
            handler(rotate_secret_event_valid, context)

    # Set the secret rotation step to finish secret
    rotate_secret_event_valid["Step"] = RotateSecretStep.FINISH_SECRET.value
    # Call the lambda function
    with patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call):
        handler(rotate_secret_event_valid, context)
