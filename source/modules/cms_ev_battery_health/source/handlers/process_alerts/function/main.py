# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json
import os
from functools import lru_cache
from typing import Any, Dict, List

# Third Party Libraries
import requests

# AWS Libraries
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

# CMS Common Library
from cms_common.auth.auth_configs import (
    CMSClientConfig,
    CMSIdPConfig,
    get_idp_config,
    get_service_client_config,
)
from cms_common.cache.ttl_cache import get_ttl_cache_check

# Connected Mobility Solution on AWS
from .lib.custom_exceptions import ClientAuthenticationError, SendAlertError

tracer = Tracer()
logger = Logger()

MAX_CACHE_SIZE_CLIENT_AUTH = 1


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

    records: List[Dict[str, Any]] = event["Records"]
    process_alerts(access_token=access_token, records=records)


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
def process_alerts(access_token: str, records: List[Dict[str, Any]]) -> None:
    api_headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {access_token}",
    }

    # send the alerts payload to the alerts endpoint
    for record in records:
        processed_alert_payloads = construct_alert_payloads_from_sns_record(
            record=record
        )

        for alert_payload in processed_alert_payloads:

            mutation = """
                mutation PublishMutation($vin: String!, $alarmType: AlarmType!, $message: String!) {
                    publish(vin: $vin, alarmType: $alarmType, message: $message) {
                        status
                        message
                    }
                }
            """

            response = requests.post(
                url=os.environ["ALERTS_PUBLISH_ENDPOINT_URL"],
                json={
                    "query": mutation,
                    "variables": alert_payload,
                },
                headers=api_headers,
                timeout=30,
            )

            if not response.ok:
                raise SendAlertError(
                    f'Error when publishing alert payload! Payload: {alert_payload}, Response {response.content.decode("utf-8")}'
                )

            logger.info(
                f"Alerts response code: {response.status_code}, Alerts response: {response.json()}"
            )


@tracer.capture_method
def construct_alert_payloads_from_sns_record(
    record: Dict[str, Any]
) -> List[Dict[str, Any]]:
    alerts = json.loads(record["Sns"]["Message"])["alerts"]
    processed_alert_payloads = []
    for alert in alerts:
        try:
            if alert["status"] != "firing":
                continue

            alert_message = (
                f'CMS EV Battery Health Alert - {alert["labels"]["alertname"]}'
            )
            vin = alert["labels"]["vin"]
            processed_alert_payloads.append(
                {
                    "vin": vin,
                    "alarmType": "EV_BATTERY_HEALTH_ALARM",
                    "message": alert_message,
                }
            )
        except KeyError:
            logger.error("Error when constructing alert payload!", exc_info=True)

    return processed_alert_payloads
