# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json
import os
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Dict

# Third Party Libraries
import boto3
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.config import Config

# Connected Mobility Solution on AWS
from .lib.custom_exceptions import ProvisioningPolicyNotFoundError
from .lib.rotate_secret_enum import RotateSecretStep, SecretStatus

if TYPE_CHECKING:
    # Third Party Libraries
    from mypy_boto3_iot.client import IoTClient
    from mypy_boto3_secretsmanager.client import SecretsManagerClient
else:
    IoTClient = object
    SecretsManagerClient = object

tracer = Tracer()
logger = Logger()


@lru_cache(maxsize=128)
def get_secrets_manager_client() -> SecretsManagerClient:
    return boto3.client(
        "secretsmanager",
        config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"]),
    )


@lru_cache(maxsize=128)
def get_iot_client() -> IoTClient:
    return boto3.client(
        "iot", config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"])
    )


# Based on the lambda function template from
# https://github.com/aws-samples/aws-secrets-manager-rotation-lambdas/blob/master/SecretsManagerRotationTemplate/lambda_function.py
@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: Dict[str, Any], context: LambdaContext) -> None:
    try:
        arn = event["SecretId"]
        token = event["ClientRequestToken"]
        step = event["Step"]
    except KeyError as err:
        logger.error("Missing key in event: %s", err, exc_info=True)
        raise

    # Ensure that rotation is enabled for this secret
    metadata = get_secrets_manager_client().describe_secret(SecretId=arn)
    if not metadata.get("RotationEnabled", False):
        raise ValueError(f"Secret {arn} is not enabled for rotation")

    # Make sure the version is staged correctly
    versions = metadata["VersionIdsToStages"]
    if token not in versions:
        raise ValueError(
            f"Secret version {token} has no stage for rotation of secret {arn}."
        )
    if SecretStatus.CURRENT.value in versions[token]:
        logger.info(
            "Secret version %s already set as AWSCURRENT for secret %s.", token, arn
        )
        return
    if SecretStatus.PENDING.value not in versions[token]:
        raise ValueError(
            f"Secret version {token} not set as AWSPENDING for rotation of secret {arn}."
        )

    # Ensure that the step parameter is valid
    if step not in {rotation_step.value for rotation_step in RotateSecretStep}:
        raise ValueError(
            "Invalid step parameter - does not correspond to a valid rotate secret step."
        )

    # Execute the function corresponding to the secret rotation step
    rotation_step_function_map = {
        RotateSecretStep.CREATE_SECRET.value: create_secret,
        RotateSecretStep.SET_SECRET.value: set_secret,
        RotateSecretStep.TEST_SECRET.value: test_secret,
        RotateSecretStep.FINISH_SECRET.value: finish_secret,
    }
    rotation_step_function_map[step](arn, token)


@tracer.capture_method
def create_secret(arn: str, token: str) -> None:
    # Make sure the current secret exists
    get_secrets_manager_client().get_secret_value(
        SecretId=arn, VersionStage=SecretStatus.CURRENT.value
    )

    # Now try to get the secret version, if that fails, put a new secret
    try:
        get_secrets_manager_client().get_secret_value(
            SecretId=arn, VersionId=token, VersionStage=SecretStatus.PENDING.value
        )
        logger.info("createSecret: Successfully retrieved secret for %s.", arn)
    except get_secrets_manager_client().exceptions.ResourceNotFoundException:
        # Generate a new secret
        new_iot_credentials = get_iot_client().create_keys_and_certificate(
            setAsActive=False
        )
        # The create_keys_and_certificate registers the certificate in DEFAULT mode
        # We want to register the certificate in SNI_ONLY mode. Hence, delete the
        # certificate from IoT and register it without CA which will create
        # the certificate in SNI_ONLY mode.
        get_iot_client().delete_certificate(
            certificateId=new_iot_credentials["certificateId"]
        )
        get_iot_client().register_certificate_without_ca(
            certificatePem=new_iot_credentials["certificatePem"], status="INACTIVE"
        )

        # Put the new secret in pending stage
        get_secrets_manager_client().put_secret_value(
            SecretId=arn,
            ClientRequestToken=token,
            SecretString=json.dumps(new_iot_credentials),
            VersionStages=[SecretStatus.PENDING.value],
        )
        logger.info(
            "createSecret: Successfully put secret for ARN %s and version %s.",
            arn,
            token,
        )


@tracer.capture_method
def set_secret(arn: str, token: str) -> None:
    # Get the current active secret containing the provisioning certificate
    current_secret = get_secrets_manager_client().get_secret_value(
        SecretId=arn,
        VersionStage=SecretStatus.CURRENT.value,
    )
    current_secret_certificate_arn = json.loads(current_secret["SecretString"])[
        "certificateArn"
    ]

    # Get the pending secret which needs to be attached to the provisioning policy
    pending_secret = get_secrets_manager_client().get_secret_value(
        SecretId=arn, VersionId=token, VersionStage=SecretStatus.PENDING.value
    )
    pending_secret_certificate_arn = json.loads(pending_secret["SecretString"])[
        "certificateArn"
    ]

    # Get the policies attached to the active provisioning certificate
    attached_policies = get_iot_client().list_attached_policies(
        target=current_secret_certificate_arn,
    )["policies"]

    # Attach the policies from current secret to the pending secret
    for policy in attached_policies:
        get_iot_client().attach_policy(
            policyName=policy["policyName"],
            target=pending_secret_certificate_arn,
        )
        logger.info(
            "Policy %s attached to pending secret %s!",
            policy["policyName"],
            pending_secret_certificate_arn,
        )


@tracer.capture_method
def test_secret(arn: str, token: str) -> None:
    # Validate that the pending secret works by checking the claim certificate policy
    # is attached to the pending secret
    pending_secret = get_secrets_manager_client().get_secret_value(
        SecretId=arn, VersionId=token, VersionStage=SecretStatus.PENDING.value
    )
    attached_policies = get_iot_client().list_attached_policies(
        target=json.loads(pending_secret["SecretString"])["certificateArn"],
    )["policies"]

    attached_policies_names = [policy["policyName"] for policy in attached_policies]

    if os.environ["CLAIM_CERT_PROVISIONING_POLICY_NAME"] not in attached_policies_names:
        raise ProvisioningPolicyNotFoundError(
            "Claim certificate provisioning policy not attached to pending secret!"
        )


@tracer.capture_method
def finish_secret(arn: str, token: str) -> None:
    # First describe the secret to get the current version
    metadata = get_secrets_manager_client().describe_secret(SecretId=arn)
    current_version = ""
    for version in metadata["VersionIdsToStages"]:
        if SecretStatus.CURRENT.value in metadata["VersionIdsToStages"][version]:
            if version == token:
                # The correct version is already marked as current, return
                logger.info(
                    "finishSecret: Version %s already marked as AWSCURRENT for %s",
                    version,
                    arn,
                )
                return
            current_version = version
            break

    # Get current certificate arn
    current_secret = get_secrets_manager_client().get_secret_value(
        SecretId=arn, VersionStage=SecretStatus.CURRENT.value
    )
    current_certificate_id = json.loads(current_secret["SecretString"])["certificateId"]
    current_certificate_arn = json.loads(current_secret["SecretString"])[
        "certificateArn"
    ]

    # Get pending certificate arn
    pending_secret_certificate_id = json.loads(
        get_secrets_manager_client().get_secret_value(
            SecretId=arn, VersionStage=SecretStatus.PENDING.value
        )["SecretString"]
    )["certificateId"]

    # Activate the pending secret's certificate
    get_iot_client().update_certificate(
        certificateId=pending_secret_certificate_id, newStatus="ACTIVE"
    )

    # Finalize by staging the pending secret version as current
    get_secrets_manager_client().update_secret_version_stage(
        SecretId=arn,
        VersionStage=SecretStatus.CURRENT.value,
        MoveToVersionId=token,
        RemoveFromVersionId=current_version,
    )
    logger.info(
        "finishSecret: Successfully set AWSCURRENT stage to version %s for secret %s.",
        token,
        arn,
    )

    # Deactivate and delete old certificate
    delete_certificate(
        certificate_id=current_certificate_id, certificate_arn=current_certificate_arn
    )


@tracer.capture_method
def delete_certificate(certificate_id: str, certificate_arn: str) -> None:
    # Deactivate the certificate
    get_iot_client().update_certificate(
        certificateId=certificate_id, newStatus="INACTIVE"
    )
    logger.info("Updated certificiate with id: %s", certificate_id)

    # Detach all policies attached to the certificate
    attached_policies = get_iot_client().list_attached_policies(target=certificate_arn)[
        "policies"
    ]
    for policy in attached_policies:
        get_iot_client().detach_policy(
            policyName=policy["policyName"],
            target=certificate_arn,
        )
        logger.info(
            "Detached policy %s from certificiate with id: %s",
            policy["policyName"],
            certificate_id,
        )

    # Delete certificate
    get_iot_client().delete_certificate(certificateId=certificate_id)
    logger.info("Deleted certificiate with id: %s", certificate_id)
