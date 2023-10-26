# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json
import os
from typing import Any, Dict, List

# Third Party Libraries
import requests
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.parameters import get_secret
from aws_lambda_powertools.utilities.typing import LambdaContext

# Connected Mobility Solution on AWS
from .lib.custom_exceptions import SendAlertError, TokenExchangeError

tracer = Tracer()
logger = Logger()


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: Dict[str, Any], context: LambdaContext) -> None:
    # send the alerts payload to the alerts endpoint
    api_headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {get_access_token()}",
    }
    for record in event["Records"]:
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

            alerts_response = requests.post(
                url=os.environ["ALERTS_PUBLISH_ENDPOINT_URL"],
                json={
                    "query": mutation,
                    "variables": alert_payload,
                },
                headers=api_headers,
                timeout=30,
            )

            if not alerts_response.ok:
                raise SendAlertError(
                    f'Error when publishing alert payload! Payload: {alert_payload}, Response {alerts_response.content.decode("utf-8")}'
                )

            logger.info(
                f"Alerts response code: {alerts_response.status_code}, Alerts response: {alerts_response.json()}"
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
        "client_secret": get_secret(
            name=os.environ["AUTHENTICATION_SERVICE_CLIENT_SECRET_ARN"], max_age=300
        ),
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
