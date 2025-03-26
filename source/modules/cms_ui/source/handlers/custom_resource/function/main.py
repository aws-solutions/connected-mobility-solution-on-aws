# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json
import os
import time
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Dict

# Third Party Libraries
import requests

# AWS Libraries
import boto3
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.config import Config

# CMS Common Library
from cms_common.enums.custom_resource import (
    CustomResourceRequestType,
    CustomResourceStatusType,
)

# Connected Mobility Solution on AWS
from .lib.custom_resource_type_enum import CustomResourceFunctionType

tracer = Tracer()
logger = Logger()

if TYPE_CHECKING:
    # Third Party Libraries
    from mypy_boto3_cognito_idp import CognitoIdentityProviderClient
    from mypy_boto3_s3 import S3Client
    from mypy_boto3_secretsmanager import SecretsManagerClient

else:
    CognitoIdentityProviderClient = object
    S3Client = object
    SecretsManagerClient = object


@lru_cache(maxsize=128)
def get_s3_client() -> S3Client:
    return boto3.client(
        "s3", config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"])
    )


@lru_cache(maxsize=128)
def get_cognito_client() -> CognitoIdentityProviderClient:
    return boto3.client(
        "cognito-idp", config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"])
    )


@lru_cache(maxsize=128)
def get_secretsmanager_client() -> SecretsManagerClient:
    return boto3.client(
        "secretsmanager",
        config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"]),
    )


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    response = {"Status": CustomResourceStatusType.SUCCESS.value, "Data": {}}

    try:
        resource_map = {
            CustomResourceFunctionType.CREATE_CONFIG.value: create_runtime_config,
            CustomResourceFunctionType.CREATE_USERPOOL_USER.value: create_userpool_user,
        }

        retry = 20
        while retry:
            try:
                response["Status"] = CustomResourceStatusType.SUCCESS.value
                response["Data"] = resource_map[
                    event["ResourceProperties"]["Resource"]
                ](event)
                retry = 0
            except Exception as exception:  # pylint: disable=broad-exception-caught
                # Wrap all exceptions so CloudFormation doesn't hang
                response["Status"] = CustomResourceStatusType.FAILED.value
                response["Data"] = {"error": str(exception)}
                logger.error(
                    "CustomResource error; retries left %s: %s", retry, exception
                )
                time.sleep(1 * retry)
                retry -= 1

        send_cloud_formation_response(
            event,
            response,
            f"See the details in CloudWatch Log Stream: {context.log_stream_name}",
        )
    except Exception as exception:  # pylint: disable=broad-exception-caught
        response["Status"] = CustomResourceStatusType.FAILED.value
        response["Data"] = {"error": str(exception)}
        send_cloud_formation_response(
            event,
            response,
            f"See the details in CloudWatch Log Stream: {context.log_stream_name}",
        )

    return response


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

    logger.info("response", extra={"response_body": response_body})

    headers = {"Content-Type": "application/json"}

    requests.put(
        event["ResponseURL"],
        data=json.dumps(response_body),
        headers=headers,
        timeout=60,
    )


# ---------------------------------------------------- CustomResources ----------------------------------------------------
@tracer.capture_method
def create_runtime_config(event: Dict[str, Any]) -> Dict[str, str]:
    if event["RequestType"] in [
        CustomResourceRequestType.CREATE.value,
        CustomResourceRequestType.UPDATE.value,
    ]:
        runtime_config = event["ResourceProperties"]["configBase"]

        idp_config_secret_arn = event["ResourceProperties"]["idpConfigSecretArn"]
        idp_config = get_idp_config(idp_config_secret_arn=idp_config_secret_arn)

        runtime_config["oAuth"]["authorizationEndpoint"] = idp_config[
            "authorization_endpoint"
        ]
        runtime_config["oAuth"]["tokenEndpoint"] = idp_config["token_endpoint"]
        runtime_config["oAuth"]["logoutEndpoint"] = idp_config["logout_endpoint"]

        runtime_config_str = json.dumps(runtime_config, separators=(",", ":"))
        get_s3_client().put_object(
            Body=runtime_config_str,
            Bucket=event["ResourceProperties"]["DestinationBucket"],
            Key=event["ResourceProperties"]["ConfigFileName"],
            ContentType="application/javascript",
        )
        logger.info(
            "created s3 obj at %s",
            event["ResourceProperties"]["DestinationBucket"],
        )
        logger.info("s3 obj: %s", runtime_config)

    return {"Bucket": event["ResourceProperties"]["DestinationBucket"]}


@tracer.capture_method
def get_idp_config(idp_config_secret_arn: str) -> Dict[str, str]:
    response = get_secretsmanager_client().get_secret_value(
        SecretId=idp_config_secret_arn
    )

    secret_value = response["SecretString"]

    secret_data = json.loads(secret_value)

    return {
        "authorization_endpoint": secret_data["authorization_endpoint"],
        "token_endpoint": secret_data["token_endpoint"],
        "logout_endpoint": secret_data["logout_endpoint"],
    }


@tracer.capture_method
def create_userpool_user(event: Dict[str, Any]) -> None:
    if event["RequestType"] in [
        CustomResourceRequestType.CREATE.value,
        CustomResourceRequestType.UPDATE.value,
    ]:
        user_pool_id = event["ResourceProperties"]["UserpoolId"]
        username = event["ResourceProperties"]["Username"]
        user_attributes = event["ResourceProperties"]["UserAttributes"]
        desired_delivery_mediums = event["ResourceProperties"]["DesiredDeliveryMediums"]
        force_alias_creation = (
            event["ResourceProperties"]["ForceAliasCreation"] == "true"
        )
        try:
            get_cognito_client().admin_create_user(
                UserPoolId=user_pool_id,
                Username=username,
                UserAttributes=user_attributes,
                ForceAliasCreation=force_alias_creation,
                DesiredDeliveryMediums=desired_delivery_mediums,
            )
        except get_cognito_client().exceptions.UsernameExistsException:
            # stack was probably executed before or user was added manually
            ...
