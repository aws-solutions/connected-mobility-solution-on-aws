# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import io
import json
import zipfile
from typing import Any, Dict, Generator

# Third Party Libraries
import boto3
import pytest
from moto import mock_aws  # type: ignore
from mypy_boto3_lambda.type_defs import FunctionConfigurationResponseTypeDef
from mypy_boto3_secretsmanager.type_defs import (
    CreateSecretResponseTypeDef,
    RotateSecretResponseTypeDef,
    UpdateSecretVersionStageResponseTypeDef,
)

# Connected Mobility Solution on AWS
from ...config.constants import EVBatteryHealthConstants
from ...handlers.rotate_secret.lib.rotate_secret_enum import SecretStatus


@pytest.fixture(name="rotate_secret_lambda_function")
def fixture_rotate_secret_lambda_function() -> (
    Generator[FunctionConfigurationResponseTypeDef, None, None]
):
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


@pytest.fixture(name="grafana_api_key_secret_rotation_enabled")
def fixture_grafana_api_key_secret_rotation_enabled(
    grafana_api_key_secret: CreateSecretResponseTypeDef,
    rotate_secret_lambda_function: FunctionConfigurationResponseTypeDef,
) -> Generator[RotateSecretResponseTypeDef, None, None]:
    secretsmanager_client = boto3.client("secretsmanager")
    secret = secretsmanager_client.rotate_secret(
        SecretId=grafana_api_key_secret["ARN"],
        ClientRequestToken=grafana_api_key_secret["VersionId"],
        RotationLambdaARN=rotate_secret_lambda_function["FunctionArn"],
        RotationRules={
            "AutomaticallyAfterDays": EVBatteryHealthConstants.GRAFANA_API_KEY_EXPIRATION_DAYS
            - 1,
        },
        RotateImmediately=False,
    )

    yield secret


@pytest.fixture(name="grafana_api_key_secret_staged_for_rotation")
def fixture_grafana_api_key_secret_staged_for_rotation(
    grafana_api_key_secret_metadata: Dict[str, Any],
    grafana_api_key_secret_rotation_enabled: RotateSecretResponseTypeDef,
) -> Generator[UpdateSecretVersionStageResponseTypeDef, None, None]:
    secretsmanager_client = boto3.client("secretsmanager")
    secretsmanager_client.update_secret(
        SecretId=grafana_api_key_secret_rotation_enabled["ARN"],
        ClientRequestToken=grafana_api_key_secret_metadata["PendingVersion"],
        SecretString=json.dumps(
            {
                "key": "test-grafana-api-key",
                "keyName": "test-grafana-api-key-name",
                "workspaceId": "test-grafana-workspace-id",
            }
        ),
    )

    secretsmanager_client.update_secret_version_stage(
        SecretId=grafana_api_key_secret_rotation_enabled["ARN"],
        VersionStage=SecretStatus.CURRENT.value,
        MoveToVersionId=grafana_api_key_secret_metadata["CurrentVersion"],
        RemoveFromVersionId=grafana_api_key_secret_metadata["PendingVersion"],
    )

    secretsmanager_client.update_secret_version_stage(
        SecretId=grafana_api_key_secret_rotation_enabled["ARN"],
        VersionStage=SecretStatus.PENDING.value,
        MoveToVersionId=grafana_api_key_secret_metadata["PendingVersion"],
    )

    grafana_api_key_secret_staged_for_rotation = (
        secretsmanager_client.update_secret_version_stage(
            SecretId=grafana_api_key_secret_rotation_enabled["ARN"],
            VersionStage=SecretStatus.PREVIOUS.value,
            RemoveFromVersionId=grafana_api_key_secret_metadata["PendingVersion"],
        )
    )
    yield grafana_api_key_secret_staged_for_rotation


@pytest.fixture(name="rotate_secret_event_rotation_not_enabled")
def fixture_rotate_secret_event_rotation_not_enabled(
    grafana_api_key_secret: CreateSecretResponseTypeDef,
) -> Generator[Dict[str, Any], None, None]:
    rotate_secret_event_rotation_not_enabled = {
        "SecretId": grafana_api_key_secret["ARN"],
        "ClientRequestToken": grafana_api_key_secret["VersionId"],
        "Step": "",
    }
    yield rotate_secret_event_rotation_not_enabled


@pytest.fixture(name="rotate_secret_event_invalid_version_to_stage")
def fixture_rotate_secret_event_invalid_version_to_stage(
    grafana_api_key_secret_rotation_enabled: RotateSecretResponseTypeDef,
) -> Generator[Dict[str, Any], None, None]:
    rotate_secret_event_invalid_version_to_stage = {
        "SecretId": grafana_api_key_secret_rotation_enabled["ARN"],
        "ClientRequestToken": "invalid-token",
        "Step": "",
    }
    yield rotate_secret_event_invalid_version_to_stage


@pytest.fixture(name="rotate_secret_event_invalid_step")
def fixture_rotate_secret_event_invalid_step(
    grafana_api_key_secret_rotation_enabled: RotateSecretResponseTypeDef,
) -> Generator[Dict[str, Any], None, None]:
    rotate_secret_event_invalid_step = {
        "SecretId": grafana_api_key_secret_rotation_enabled["ARN"],
        "ClientRequestToken": grafana_api_key_secret_rotation_enabled["VersionId"],
        "Step": "",
    }
    yield rotate_secret_event_invalid_step


@pytest.fixture(name="rotate_secret_event_valid")
def fixture_rotate_secret_event_valid(
    grafana_api_key_secret_staged_for_rotation: UpdateSecretVersionStageResponseTypeDef,
    grafana_api_key_secret_metadata: Dict[str, Any],
) -> Generator[Dict[str, Any], None, None]:
    rotate_secret_event_valid = {
        "SecretId": grafana_api_key_secret_staged_for_rotation["ARN"],
        "ClientRequestToken": grafana_api_key_secret_metadata["PendingVersion"],
        "Step": "",  # Set the appropriate step in the tests
    }
    yield rotate_secret_event_valid
