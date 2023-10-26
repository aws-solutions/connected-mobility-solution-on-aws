# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json
from typing import Any, Dict, Generator

# Third Party Libraries
import boto3
import pytest
from moto import mock_iot, mock_secretsmanager  # type: ignore
from mypy_boto3_iot.type_defs import CreatePolicyResponseTypeDef
from mypy_boto3_lambda.type_defs import FunctionConfigurationResponseTypeDef
from mypy_boto3_secretsmanager.type_defs import (
    CreateSecretResponseTypeDef,
    RotateSecretResponseTypeDef,
    UpdateSecretVersionStageResponseTypeDef,
)

# Connected Mobility Solution on AWS
from ....handlers.rotate_secret.lib.rotate_secret_enum import SecretStatus


@pytest.fixture(name="provisioning_secret_metadata")
def fixture_provisioning_secret_metadata() -> Dict[str, Any]:
    return {
        "SecretName": "test-secret-name",
        "CurrentVersion": "test-current-secret-token-123456",  # min length of token should be 32
        "PendingVersion": "test-pending-secret-token-123456",
    }


@pytest.fixture(name="provisioning_policy")
def fixture_provisioning_policy() -> Generator[CreatePolicyResponseTypeDef, None, None]:
    with mock_iot():
        iot_client = boto3.client("iot")
        provisioning_policy = iot_client.create_policy(
            policyName="claim-certificate-provisioning-policy",
            policyDocument=json.dumps(
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Action": ["iot:CreateKeysAndCertificate"],
                            "Resource": ["*"],
                        }
                    ],
                }
            ),
        )
        yield provisioning_policy


@pytest.fixture(name="provisioning_secret")
def fixture_provisioning_secret(
    provisioning_secret_metadata: Dict[str, Any],
    provisioning_policy: CreatePolicyResponseTypeDef,
) -> Generator[CreateSecretResponseTypeDef, None, None]:
    with mock_secretsmanager():
        secretsmanager_client = boto3.client("secretsmanager")
        iot_client = boto3.client("iot")

        iot_credentials = iot_client.create_keys_and_certificate(setAsActive=True)
        # attach provisioning policy to certificate
        iot_client.attach_policy(
            policyName=provisioning_policy["policyName"],
            target=iot_credentials["certificateArn"],
        )

        secret = secretsmanager_client.create_secret(
            Name=provisioning_secret_metadata["SecretName"],
            ClientRequestToken=provisioning_secret_metadata["CurrentVersion"],
            SecretString=json.dumps(iot_credentials),
        )

        yield secret


@pytest.fixture(name="provisioning_secret_rotation_enabled")
def fixture_provisioning_secret_rotation_enabled(
    provisioning_secret: CreateSecretResponseTypeDef,
    rotate_secret_lambda_function: FunctionConfigurationResponseTypeDef,
) -> Generator[RotateSecretResponseTypeDef, None, None]:
    secretsmanager_client = boto3.client("secretsmanager")
    secret = secretsmanager_client.rotate_secret(
        SecretId=provisioning_secret["ARN"],
        ClientRequestToken=provisioning_secret["VersionId"],
        RotationLambdaARN=rotate_secret_lambda_function["FunctionArn"],
        RotationRules={
            "AutomaticallyAfterDays": 90,
        },
        RotateImmediately=False,
    )

    yield secret


@pytest.fixture(name="provisioning_secret_staged_for_rotation")
def fixture_provisioning_secret_staged_for_rotation(
    provisioning_policy: CreatePolicyResponseTypeDef,
    provisioning_secret_metadata: Dict[str, Any],
    provisioning_secret_rotation_enabled: RotateSecretResponseTypeDef,
) -> Generator[UpdateSecretVersionStageResponseTypeDef, None, None]:
    secretsmanager_client = boto3.client("secretsmanager")
    iot_client = boto3.client("iot")

    # create new iot credentials to update the secret with
    iot_credentials = iot_client.create_keys_and_certificate(setAsActive=True)
    # attach provisioning policy to certificate
    iot_client.attach_policy(
        policyName=provisioning_policy["policyName"],
        target=iot_credentials["certificateArn"],
    )
    secretsmanager_client.update_secret(
        SecretId=provisioning_secret_rotation_enabled["ARN"],
        ClientRequestToken=provisioning_secret_metadata["PendingVersion"],
        SecretString=json.dumps(iot_credentials),
    )

    secretsmanager_client.update_secret_version_stage(
        SecretId=provisioning_secret_rotation_enabled["ARN"],
        VersionStage=SecretStatus.CURRENT.value,
        MoveToVersionId=provisioning_secret_metadata["CurrentVersion"],
        RemoveFromVersionId=provisioning_secret_metadata["PendingVersion"],
    )

    secretsmanager_client.update_secret_version_stage(
        SecretId=provisioning_secret_rotation_enabled["ARN"],
        VersionStage=SecretStatus.PENDING.value,
        MoveToVersionId=provisioning_secret_metadata["PendingVersion"],
    )

    provisioning_secret_staged_for_rotation = (
        secretsmanager_client.update_secret_version_stage(
            SecretId=provisioning_secret_rotation_enabled["ARN"],
            VersionStage=SecretStatus.PREVIOUS.value,
            RemoveFromVersionId=provisioning_secret_metadata["PendingVersion"],
        )
    )
    yield provisioning_secret_staged_for_rotation


@pytest.fixture(name="rotate_secret_event_rotation_not_enabled")
def fixture_rotate_secret_event_rotation_not_enabled(
    provisioning_secret: CreateSecretResponseTypeDef,
) -> Generator[Dict[str, Any], None, None]:
    rotate_secret_event_rotation_not_enabled = {
        "SecretId": provisioning_secret["ARN"],
        "ClientRequestToken": provisioning_secret["VersionId"],
        "Step": "",
    }
    yield rotate_secret_event_rotation_not_enabled


@pytest.fixture(name="rotate_secret_event_invalid_version_to_stage")
def fixture_rotate_secret_event_invalid_version_to_stage(
    provisioning_secret_rotation_enabled: RotateSecretResponseTypeDef,
) -> Generator[Dict[str, Any], None, None]:
    rotate_secret_event_invalid_version_to_stage = {
        "SecretId": provisioning_secret_rotation_enabled["ARN"],
        "ClientRequestToken": "invalid-token",
        "Step": "",
    }
    yield rotate_secret_event_invalid_version_to_stage


@pytest.fixture(name="rotate_secret_event_invalid_step")
def fixture_rotate_secret_event_invalid_step(
    provisioning_secret_rotation_enabled: RotateSecretResponseTypeDef,
) -> Generator[Dict[str, Any], None, None]:
    rotate_secret_event_invalid_step = {
        "SecretId": provisioning_secret_rotation_enabled["ARN"],
        "ClientRequestToken": provisioning_secret_rotation_enabled["VersionId"],
        "Step": "",
    }
    yield rotate_secret_event_invalid_step


@pytest.fixture(name="rotate_secret_event_valid")
def fixture_rotate_secret_event_valid(
    provisioning_secret_staged_for_rotation: UpdateSecretVersionStageResponseTypeDef,
    provisioning_secret_metadata: Dict[str, Any],
) -> Generator[Dict[str, Any], None, None]:
    rotate_secret_event_valid = {
        "SecretId": provisioning_secret_staged_for_rotation["ARN"],
        "ClientRequestToken": provisioning_secret_metadata["PendingVersion"],
        "Step": "",  # Set the appropriate step in the tests
    }
    yield rotate_secret_event_valid
