# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Dict

# Third Party Libraries
import boto3
import requests
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.config import Config

# Connected Mobility Solution on AWS
from .lib.custom_exceptions import SendAlertError, TokenExchangeError

if TYPE_CHECKING:
    # Third Party Libraries
    from mypy_boto3_secretsmanager.client import SecretsManagerClient
else:
    SecretsManagerClient = object
    LambdaClient = object

tracer = Tracer()
logger = Logger()


@lru_cache(maxsize=128)
def get_secrets_manager_client() -> SecretsManagerClient:
    return boto3.client(
        "secretsmanager",
        config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"]),
    )


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: Dict[str, Any], context: LambdaContext) -> None:
    mutation = """
        mutation PublishMutation($vin: String!, $alarmType: AlarmType!, $message: String!) {
            publish(vin: $vin, alarmType: $alarmType, message: $message) {
                status
                message
            }
        }
    """

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": "Bearer " + get_access_token(),
    }

    response = requests.post(
        os.environ["ALERTS_PUBLISH_ENDPOINT_URL"],
        json={
            "query": mutation,
            "variables": {
                "vin": event["vin"],
                "alarmType": "VEHICLE_ALARM",
                "message": event["message"],
            },
        },
        headers=headers,
        timeout=30,
    )

    if not response.ok:
        raise SendAlertError(
            f'Error when sending alert to endpoint: {response.content.decode("utf-8")}'
        )

    logger.info(
        f"Alerts response code: {response.status_code}, Alerts response: {response.json()}"
    )


@tracer.capture_method
def get_token_url() -> str:
    user_pool_domain = os.environ["AUTHENTICATION_USER_POOL_DOMAIN"]
    user_pool_region = os.environ["AUTHENTICATION_USER_POOL_REGION"]
    return f"https://{user_pool_domain}.auth.{user_pool_region}.amazoncognito.com/oauth2/token"


@tracer.capture_method
def get_access_token() -> str:
    token_exchange_payload = {
        "grant_type": "client_credentials",
        "client_id": os.environ["AUTHENTICATION_SERVICE_CLIENT_ID"],
        "client_secret": get_secrets_manager_client().get_secret_value(
            SecretId=os.environ["AUTHENTICATION_SERVICE_CLIENT_SECRET_ARN"]
        )["SecretString"],
        "scope": f'{os.environ["AUTHENTICATION_RESOURCE_SERVER_ID"]}/{os.environ["AUTHENTICATION_SERVICE_CALLER_SCOPE"]}',
    }

    token_exchange_response = requests.post(
        url=get_token_url(),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=token_exchange_payload,
        timeout=10,
    )

    if not token_exchange_response.ok:
        raise TokenExchangeError(
            f'Error when getting access token for authentication: {token_exchange_response.content.decode("utf-8")}'
        )

    return str(token_exchange_response.json()["access_token"])
