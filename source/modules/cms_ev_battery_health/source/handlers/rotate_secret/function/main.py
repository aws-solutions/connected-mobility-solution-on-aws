# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json
import os
import uuid
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Dict

# Third Party Libraries
import requests

# AWS Libraries
import boto3
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.config import Config
from botocore.exceptions import ClientError

# Connected Mobility Solution on AWS
from .lib.custom_exceptions import (
    GrafanaApiError,
    InvalidSecretRotationStepError,
    SecretRotationNotEnabledError,
    SecretRotationNotStagedError,
)
from .lib.rotate_secret_enum import RotateSecretStep, SecretStatus

if TYPE_CHECKING:
    # Third Party Libraries
    from mypy_boto3_grafana.client import ManagedGrafanaClient
    from mypy_boto3_secretsmanager.client import SecretsManagerClient
else:
    SecretsManagerClient = object
    ManagedGrafanaClient = object

tracer = Tracer()
logger = Logger()


@lru_cache(maxsize=128)
def get_secrets_manager_client() -> SecretsManagerClient:
    return boto3.client(
        "secretsmanager",
        config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"]),
    )


@lru_cache(maxsize=128)
def get_grafana_client() -> ManagedGrafanaClient:
    return boto3.client(
        "grafana", config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"])
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
        raise SecretRotationNotEnabledError(f"Secret {arn} is not enabled for rotation")

    # Make sure the version is staged correctly
    versions = metadata["VersionIdsToStages"]
    if token not in versions:
        raise SecretRotationNotStagedError(
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
        raise InvalidSecretRotationStepError(
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
    current_secret_dict = json.loads(
        get_secrets_manager_client().get_secret_value(
            SecretId=arn, VersionStage=SecretStatus.CURRENT.value
        )["SecretString"]
    )

    # Now try to get the secret version, if that fails, put a new secret
    try:
        get_secrets_manager_client().get_secret_value(
            SecretId=arn, VersionId=token, VersionStage=SecretStatus.PENDING.value
        )
        logger.info("createSecret: Successfully retrieved secret for %s.", arn)
    except ClientError:
        # Generate a new secret
        workspace_id = current_secret_dict["workspaceId"]

        pending_api_key = get_grafana_client().create_workspace_api_key(
            keyName=str(uuid.uuid4()),
            keyRole="ADMIN",
            secondsToLive=int(os.environ["GRAFANA_API_KEY_EXPIRATION_DAYS"])
            * 24
            * 60
            * 60,  # 30 days is the maximum validity
            workspaceId=workspace_id,
        )

        # Put the new secret in pending stage
        get_secrets_manager_client().put_secret_value(
            SecretId=arn,
            ClientRequestToken=token,
            SecretString=json.dumps(pending_api_key),
            VersionStages=[SecretStatus.PENDING.value],
        )
        logger.info(
            "createSecret: Successfully put secret for ARN %s and version %s.",
            arn,
            token,
        )


@tracer.capture_method
def set_secret(arn: str, token: str) -> None:
    logger.info(
        "setSecret: Successfully set secret for ARN %s and version %s.",
        arn,
        token,
    )


@tracer.capture_method
def test_secret(arn: str, token: str) -> None:
    # Get the pending secret containing the new api key
    pending_secret_dict = json.loads(
        get_secrets_manager_client().get_secret_value(
            SecretId=arn, VersionId=token, VersionStage=SecretStatus.PENDING.value
        )["SecretString"]
    )

    # Validate that the api key works by using it to call a grafana api
    response = requests.get(
        url=f"https://{os.environ['GRAFANA_WORKSPACE_ENDPOINT']}/api/org/",
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {pending_secret_dict['key']}",
        },
        timeout=10,
    )
    if not response.ok:
        raise GrafanaApiError(response.text)


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

    # Get old api key
    current_secret_dict = json.loads(
        get_secrets_manager_client().get_secret_value(
            SecretId=arn, VersionStage=SecretStatus.CURRENT.value
        )["SecretString"]
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

    # delete old api key
    get_grafana_client().delete_workspace_api_key(
        keyName=current_secret_dict["keyName"],
        workspaceId=current_secret_dict["workspaceId"],
    )
    logger.info("finishSecret: Deleted previous api key from grafana.")
