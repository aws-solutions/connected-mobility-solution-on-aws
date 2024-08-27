# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
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
from cms_common.auth.auth_configs import (
    CMSClientConfig,
    CMSIdPConfig,
    get_idp_config,
    get_service_client_config,
)
from cms_common.cache.ttl_cache import get_ttl_cache_check

# Connected Mobility Solution on AWS
from .lib.custom_exceptions import ClientAuthenticationError, VehicleTriggerAlarmError

if TYPE_CHECKING:
    # Third Party Libraries
    from mypy_boto3_ssm import SSMClient
else:
    SSMClient = object

tracer = Tracer()
logger = Logger()

MAX_CACHE_SIZE_CLIENT_AUTH = 1
MAX_CACHE_SIZE_BOTO_CLIENT = 10
MAX_CACHE_SIZE_SSM_PARAMETERS = 128


@lru_cache(maxsize=MAX_CACHE_SIZE_BOTO_CLIENT)
def get_ssm_client() -> SSMClient:
    return boto3.client(
        "ssm",
        config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"]),
    )


@lru_cache(maxsize=MAX_CACHE_SIZE_SSM_PARAMETERS)
def get_ssm_parameter(ssm_name: str) -> str:
    return get_ssm_client().get_parameter(Name=ssm_name, WithDecryption=True,)[
        "Parameter"
    ]["Value"]


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: Dict[str, Any], context: LambdaContext) -> None:
    idp_config = get_idp_config_from_common(
        user_agent_string=os.environ["USER_AGENT_STRING"],
        identity_provider_id=os.environ["IDENTITY_PROVIDER_ID"],
    )

    client_config = get_service_client_config_from_common(
        user_agent_string=os.environ["USER_AGENT_STRING"],
        identity_provider_id=os.environ["IDENTITY_PROVIDER_ID"],
    )
    access_token = get_access_token(idp_config, client_config)

    response = post_mutation(access_token=access_token, event=event)

    if not response.ok:
        get_ssm_parameter.cache_clear()
        raise VehicleTriggerAlarmError(
            f'Error when sending alert to endpoint: {response.content.decode("utf-8")}'
        )

    logger.info(
        f"Alerts response code: {response.status_code}, Alerts response: {response.json()}"
    )


@lru_cache(maxsize=MAX_CACHE_SIZE_CLIENT_AUTH)
@tracer.capture_method
def get_service_client_config_from_common(
    user_agent_string: str,
    identity_provider_id: str,
    ttl_cache_check: int = get_ttl_cache_check(),  # Add a TTL to cache in case of SSM or Secrets Manager value changes.
) -> CMSClientConfig:
    return get_service_client_config(
        user_agent_string=user_agent_string,
        identity_provider_id=identity_provider_id,
    )


@lru_cache(maxsize=MAX_CACHE_SIZE_CLIENT_AUTH)
@tracer.capture_method
def get_idp_config_from_common(
    user_agent_string: str,
    identity_provider_id: str,
    ttl_cache_check: int = get_ttl_cache_check(),  # Add a TTL to cache in case of SSM or Secrets Manager value changes.
) -> CMSIdPConfig:
    return get_idp_config(
        user_agent_string=user_agent_string,
        identity_provider_id=identity_provider_id,
    )


@lru_cache(maxsize=MAX_CACHE_SIZE_CLIENT_AUTH)
@tracer.capture_method
def get_access_token(idp_config: CMSIdPConfig, client_config: CMSClientConfig) -> str:
    client_credentials_payload = {
        "grant_type": "client_credentials",
        "audience": client_config.audience,
        "client_id": client_config.client_id,
        "client_secret": client_config.client_secret,
    }

    client_credentials_flow_response = requests.post(
        url=idp_config.token_endpoint,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data=client_credentials_payload,
        timeout=10,
    )

    if not client_credentials_flow_response.ok:
        raise ClientAuthenticationError(
            f'Error when getting access token for authentication: {client_credentials_flow_response.content.decode("utf-8")}'
        )

    return str(client_credentials_flow_response.json()["access_token"])


@tracer.capture_method
def post_mutation(access_token: str, event: Dict[str, Any]) -> requests.Response:
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
        "Authorization": f"Bearer {access_token}",
    }

    response = requests.post(
        get_ssm_parameter(os.environ["ALERTS_PUBLISH_ENDPOINT_URL_PARAMETER"]),
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

    return response
