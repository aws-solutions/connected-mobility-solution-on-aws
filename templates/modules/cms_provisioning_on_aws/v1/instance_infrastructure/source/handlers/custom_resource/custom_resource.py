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
import boto3
import requests
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.config import Config

# Connected Mobility Solution on AWS
from .lib.custom_resource_type_enum import CustomResourceType

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
def get_iot_client() -> IoTClient:
    return boto3.client(
        "iot", config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"])
    )


@lru_cache(maxsize=128)
def get_secrets_manager_client() -> SecretsManagerClient:
    return boto3.client(
        "secretsmanager",
        config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"]),
    )


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    response = {"Status": CustomResourceType.StatusType.FAILED.value, "Data": {}}

    resource_map = {
        CustomResourceType.ResourceType.LOAD_OR_CREATE_IOT_CREDENTIALS.value: load_or_create_iot_credentials,
        CustomResourceType.ResourceType.UPDATE_EVENT_CONFIGURATIONS.value: update_event_configurations,
        CustomResourceType.ResourceType.DELETE_PROVISIONING_CERTIFICATE.value: delete_provisioning_certificate,
    }

    try:
        response["Data"] = resource_map[event["ResourceProperties"]["Resource"]](event)  # type: ignore
        response["Status"] = CustomResourceType.StatusType.SUCCESS.value
    except Exception as exception:  # pylint: disable=W0703
        # Wrap all exceptions so CloudFormation doesn't hang
        logger.error("CustomResource error: %s", exception, exc_info=True)

    send_cloud_formation_response(
        event,
        response,
        f"See the details in CloudWatch Log Stream: {context.log_stream_name}",
    )

    return response


# Enable IoT event messaging, this is necessary for our post_provision lambda to trigger
@tracer.capture_method
def update_event_configurations(event: Dict[str, Any]) -> None:
    if event["RequestType"] in [
        CustomResourceType.RequestType.CREATE.value,
        CustomResourceType.RequestType.UPDATE.value,
    ]:
        get_iot_client().update_event_configurations(
            eventConfigurations={"THING": {"Enabled": True}}
        )


@tracer.capture_method
def send_cloud_formation_response(
    event: Dict[str, Any], response: Dict[str, Any], reason: str
) -> None:
    response_body = {
        "Status": response["Status"],
        "Reason": reason,
        "PhysicalResourceId": event["LogicalResourceId"],
        "StackId": event["StackId"],
        "RequestId": event["RequestId"],
        "LogicalResourceId": event["LogicalResourceId"],
        "Data": response["Data"],
    }

    headers = {"Content-Type": "application/json"}

    requests.put(
        event["ResponseURL"],
        data=json.dumps(response_body),
        headers=headers,
        timeout=60,
    )


@tracer.capture_method
def store_iot_credentials_as_secret(
    credentials_secret_id: str, rotate_secret_lambda_arn: str
) -> Dict[str, Any]:
    iot_credentials = get_iot_client().create_keys_and_certificate(setAsActive=False)

    # delete the certificate from IoT Core to not get an AlreadyExists error
    # when the deploy process tries to create the CfnCertificate resource
    get_iot_client().delete_certificate(certificateId=iot_credentials["certificateId"])

    # create provisioning credentials secret
    secret = get_secrets_manager_client().create_secret(
        Name=credentials_secret_id,
        ClientRequestToken=str(uuid.uuid4()),
        Description="IoT certificate and key pair to be used when provisioning vehicle.",
        SecretString=json.dumps(iot_credentials),
    )

    get_secrets_manager_client().rotate_secret(
        SecretId=secret["ARN"],
        ClientRequestToken=str(uuid.uuid4()),
        RotationLambdaARN=rotate_secret_lambda_arn,
        RotationRules={
            "AutomaticallyAfterDays": 90,
        },
        RotateImmediately=False,
    )

    return iot_credentials  # type: ignore[return-value]


@tracer.capture_method
def load_or_create_iot_credentials(event: Dict[str, Any]) -> Dict[str, Any]:
    response: Dict[str, Any] = {}
    if event["RequestType"] in [
        CustomResourceType.RequestType.CREATE.value,
        CustomResourceType.RequestType.UPDATE.value,
    ]:
        # Begin loading or creating IoT Credentials to be stored in SecretsManagers
        credentials_secret_id = event["ResourceProperties"]["IoTCredentialsSecretId"]
        rotate_secret_lambda_arn = event["ResourceProperties"]["RotateSecretLambdaARN"]
        try:
            secret = get_secrets_manager_client().get_secret_value(
                SecretId=credentials_secret_id
            )
            logger.info("Using certificate that was already created!")
            response["CERTIFICATE_PEM"] = json.loads(secret["SecretString"])[
                "certificatePem"
            ]
        except get_secrets_manager_client().exceptions.ResourceNotFoundException as err:
            logger.info(
                "IoT credentials secret not found! %s \nCreating new certificate and key pair.",
                err,
            )
            iot_credentials = store_iot_credentials_as_secret(
                credentials_secret_id=credentials_secret_id,
                rotate_secret_lambda_arn=rotate_secret_lambda_arn,
            )
            response["CERTIFICATE_PEM"] = iot_credentials["certificatePem"]

    return response


@tracer.capture_method
def delete_provisioning_certificate(event: Dict[str, Any]) -> None:
    if event["RequestType"] == CustomResourceType.RequestType.DELETE.value:
        try:
            iot_targets = get_iot_client().list_targets_for_policy(
                policyName=event["ResourceProperties"]["IoTPolicyName"]
            )

            for target in iot_targets["targets"]:
                get_iot_client().detach_policy(
                    policyName=event["ResourceProperties"]["IoTPolicyName"],
                    target=target,
                )

                if is_cert(arn=target):
                    certificate_id = target.split("/")[-1]
                    get_iot_client().update_certificate(
                        certificateId=certificate_id,
                        newStatus="INACTIVE",
                    )
                    get_iot_client().delete_certificate(
                        certificateId=certificate_id,
                    )

                logger.info(
                    "%s is detached from %s",
                    target,
                    event["ResourceProperties"]["IoTPolicyName"],
                )
        except get_iot_client().exceptions.ResourceNotFoundException as exc:
            logger.error(
                "Policy with policy name: %s not found to detach!. Error: %s",
                event["ResourceProperties"]["IoTPolicyName"],
                exc,
                exc_info=True,
            )


@tracer.capture_method
def is_cert(arn: str) -> bool:
    resource_prefix = arn.split("/")[0]
    return resource_prefix.split(":")[-1] == "cert"
