# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0


# Standard Library
# mypy: disable-error-code=misc
import json
from typing import Any, Dict

# Third Party Libraries
import boto3
import pytest
from aws_lambda_powertools.utilities.typing import LambdaContext
from mypy_boto3_iot.type_defs import CreatePolicyResponseTypeDef

# Connected Mobility Solution on AWS
from ....handlers.rotate_secret.lib.custom_exceptions import (
    ProvisioningPolicyNotFoundError,
)
from ....handlers.rotate_secret.lib.rotate_secret_enum import (
    RotateSecretStep,
    SecretStatus,
)
from ....handlers.rotate_secret.rotate_secret import handler


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
    with pytest.raises(ValueError):
        handler(rotate_secret_event_rotation_not_enabled, context)


def test_handler_invalid_version_to_stage(
    rotate_secret_event_invalid_version_to_stage: Dict[str, Any],
    context: LambdaContext,
) -> None:
    with pytest.raises(ValueError):
        handler(rotate_secret_event_invalid_version_to_stage, context)


def test_handler_invalid_step(
    rotate_secret_event_invalid_step: Dict[str, Any],
    context: LambdaContext,
) -> None:
    with pytest.raises(ValueError):
        handler(rotate_secret_event_invalid_step, context)


def test_handler_create_secret_step_succeeds(
    rotate_secret_event_valid: Dict[str, Any], context: LambdaContext
) -> None:
    # Set the secret rotation step to create secret
    rotate_secret_event_valid["Step"] = RotateSecretStep.CREATE_SECRET.value
    # Call the lambda function
    handler(rotate_secret_event_valid, context)

    # The create secret step should have put a new iot credentials in the pending secret version
    secretsmanager_client = boto3.client("secretsmanager")
    pending_secret_string = secretsmanager_client.get_secret_value(
        SecretId=rotate_secret_event_valid["SecretId"]
    )["SecretString"]

    # Assert that the secret was appropriately created
    pending_secret_dict = json.loads(pending_secret_string)
    assert "certificateArn" in pending_secret_dict
    assert "certificateId" in pending_secret_dict
    assert "certificatePem" in pending_secret_dict
    assert "keyPair" in pending_secret_dict


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
    handler(rotate_secret_event_valid, context)

    # Set the secret rotation step to set secret
    rotate_secret_event_valid["Step"] = RotateSecretStep.SET_SECRET.value
    # Call the lambda function
    handler(rotate_secret_event_valid, context)

    # The set secret step should have attached all the policies attached to the current
    # secret's certificate to the pending secret's certificate
    secretsmanager_client = boto3.client("secretsmanager")
    iot_client = boto3.client("iot")
    current_certificate_arn = json.loads(
        secretsmanager_client.get_secret_value(
            SecretId=rotate_secret_event_valid["SecretId"],
            VersionStage=SecretStatus.CURRENT.value,
        )["SecretString"]
    )["certificateArn"]
    current_certificate_policies = iot_client.list_attached_policies(
        target=current_certificate_arn
    )["policies"]

    pending_certificate_arn = json.loads(
        secretsmanager_client.get_secret_value(
            SecretId=rotate_secret_event_valid["SecretId"],
            VersionStage=SecretStatus.PENDING.value,
            VersionId=rotate_secret_event_valid["ClientRequestToken"],
        )["SecretString"]
    )["certificateArn"]
    pending_certificate_policies = iot_client.list_attached_policies(
        target=pending_certificate_arn
    )["policies"]

    # Assert that the attached policies to the current and pending secrets are the same
    assert len(current_certificate_policies) > 0
    assert len(pending_certificate_policies) > 0
    assert current_certificate_policies == pending_certificate_policies


def test_handler_test_secret_step_succeeds(
    provisioning_policy: CreatePolicyResponseTypeDef,
    rotate_secret_event_valid: Dict[str, Any],
    context: LambdaContext,
) -> None:
    # Set the secret rotation step to create secret
    rotate_secret_event_valid["Step"] = RotateSecretStep.CREATE_SECRET.value
    # Call the lambda function
    handler(rotate_secret_event_valid, context)

    # Set the secret rotation step to set secret
    rotate_secret_event_valid["Step"] = RotateSecretStep.SET_SECRET.value
    # Call the lambda function
    handler(rotate_secret_event_valid, context)

    # Set the secret rotation step to test secret
    rotate_secret_event_valid["Step"] = RotateSecretStep.TEST_SECRET.value
    # Call the lambda function
    handler(rotate_secret_event_valid, context)

    # The test secret step should have validated that the provisioning policy is attached
    # to the pending secret's certificate
    secretsmanager_client = boto3.client("secretsmanager")
    iot_client = boto3.client("iot")

    pending_certificate_arn = json.loads(
        secretsmanager_client.get_secret_value(
            SecretId=rotate_secret_event_valid["SecretId"],
            VersionStage=SecretStatus.PENDING.value,
            VersionId=rotate_secret_event_valid["ClientRequestToken"],
        )["SecretString"]
    )["certificateArn"]
    pending_certificate_policies = iot_client.list_attached_policies(
        target=pending_certificate_arn
    )["policies"]

    # Assert that the provisioning policy is present in the pending secret's certificate
    assert provisioning_policy["policyName"] in [
        policy["policyName"] for policy in pending_certificate_policies
    ]


def test_handler_test_secret_step_fails(
    provisioning_policy: CreatePolicyResponseTypeDef,
    rotate_secret_event_valid: Dict[str, Any],
    context: LambdaContext,
) -> None:
    # Set the secret rotation step to create secret
    rotate_secret_event_valid["Step"] = RotateSecretStep.CREATE_SECRET.value
    # Call the lambda function
    handler(rotate_secret_event_valid, context)

    # Set the secret rotation step to set secret
    rotate_secret_event_valid["Step"] = RotateSecretStep.SET_SECRET.value
    # Call the lambda function
    handler(rotate_secret_event_valid, context)

    # The test secret step should fail if the provisioning secret is not attached
    # to the pending secret's certificate
    secretsmanager_client = boto3.client("secretsmanager")
    iot_client = boto3.client("iot")

    pending_certificate_arn = json.loads(
        secretsmanager_client.get_secret_value(
            SecretId=rotate_secret_event_valid["SecretId"],
            VersionStage=SecretStatus.PENDING.value,
            VersionId=rotate_secret_event_valid["ClientRequestToken"],
        )["SecretString"]
    )["certificateArn"]

    # Detach the provisioning policy from the pending secret's certificate and
    # assert that the test secret step fails
    iot_client.detach_policy(
        policyName=provisioning_policy["policyName"],
        target=pending_certificate_arn,
    )

    # Set the secret rotation step to test secret
    rotate_secret_event_valid["Step"] = RotateSecretStep.TEST_SECRET.value
    # Call the lambda function
    with pytest.raises(ProvisioningPolicyNotFoundError):
        handler(rotate_secret_event_valid, context)


def test_handler_finish_secret_step_succeeds(
    provisioning_policy: CreatePolicyResponseTypeDef,
    rotate_secret_event_valid: Dict[str, Any],
    context: LambdaContext,
) -> None:
    # Set the secret rotation step to create secret
    rotate_secret_event_valid["Step"] = RotateSecretStep.CREATE_SECRET.value
    # Call the lambda function
    handler(rotate_secret_event_valid, context)

    # Set the secret rotation step to set secret
    rotate_secret_event_valid["Step"] = RotateSecretStep.SET_SECRET.value
    # Call the lambda function
    handler(rotate_secret_event_valid, context)

    # Set the secret rotation step to test secret
    rotate_secret_event_valid["Step"] = RotateSecretStep.TEST_SECRET.value
    # Call the lambda function
    handler(rotate_secret_event_valid, context)

    # Set the secret rotation step to finish secret
    rotate_secret_event_valid["Step"] = RotateSecretStep.FINISH_SECRET.value
    # Call the lambda function
    handler(rotate_secret_event_valid, context)

    # The finish secret should have staged the pending secret as the
    # current secret and deactivated and deleted the old certificate.
    secretsmanager_client = boto3.client("secretsmanager")
    iot_client = boto3.client("iot")

    rotated_certificate_arn = json.loads(
        secretsmanager_client.get_secret_value(
            SecretId=rotate_secret_event_valid["SecretId"],
            VersionStage=SecretStatus.CURRENT.value,
            VersionId=rotate_secret_event_valid["ClientRequestToken"],
        )["SecretString"]
    )["certificateArn"]
    rotated_certificate_policies = iot_client.list_attached_policies(
        target=rotated_certificate_arn
    )["policies"]

    # Assert that the provisioning policy is present in the pending secret's certificate
    assert provisioning_policy["policyName"] in [
        policy["policyName"] for policy in rotated_certificate_policies
    ]

    # Assert that the previous secret's certificate was deactivated and deleted
    previous_certificate_arn = json.loads(
        secretsmanager_client.get_secret_value(
            SecretId=rotate_secret_event_valid["SecretId"],
            VersionStage=SecretStatus.PREVIOUS.value,
        )["SecretString"]
    )["certificateArn"]

    all_certificates = iot_client.list_certificates()["certificates"]
    assert previous_certificate_arn not in [
        certificate["certificateArn"] for certificate in all_certificates
    ]
