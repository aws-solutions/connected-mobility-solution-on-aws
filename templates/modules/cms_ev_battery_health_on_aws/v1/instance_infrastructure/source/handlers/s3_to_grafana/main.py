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
import requests
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.config import Config

# Connected Mobility Solution on AWS
from .lib.custom_exceptions import GrafanaApiError

if TYPE_CHECKING:
    # Third Party Libraries
    from mypy_boto3_s3.client import S3Client
    from mypy_boto3_secretsmanager.client import SecretsManagerClient
else:
    SecretsManagerClient = object
    S3Client = object

tracer = Tracer()
logger = Logger()


@lru_cache(maxsize=128)
def get_secrets_manager_client() -> SecretsManagerClient:
    return boto3.client(
        "secretsmanager",
        config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"]),
    )


@lru_cache(maxsize=128)
def get_s3_client() -> S3Client:
    return boto3.client(
        "s3", config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"])
    )


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: Dict[str, Any], context: LambdaContext) -> None:
    # This lambda function is triggered by PutObject events from S3.
    # Updates Grafana dashboards or alerts based on the
    # prefix of the object put in the S3 bucket

    grafana_api_key_secret_arn = os.environ["GRAFANA_API_KEY_SECRET_ARN"]
    grafana_workspace_endpoint = os.environ["GRAFANA_WORKSPACE_ENDPOINT"]

    dashboard_object_prefix = os.environ["DASHBOARD_S3_OBJECT_KEY_PREFIX"]
    alerts_object_prefix = os.environ["ALERTS_S3_OBJECT_KEY_PREFIX"]

    for record in event["Records"]:
        bucket = record["s3"]["bucket"]["name"]
        object_key = record["s3"]["object"]["key"]

        # load the json file from s3
        s3_object = get_s3_client().get_object(Bucket=bucket, Key=object_key)
        object_json = json.loads(s3_object["Body"].read().decode("utf-8"))

        # get the grafana api key stored in the secret
        api_key = json.loads(
            get_secrets_manager_client().get_secret_value(
                SecretId=grafana_api_key_secret_arn,
            )["SecretString"]
        )["key"]

        api_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        object_prefix_to_update_function = {
            dashboard_object_prefix: update_grafana_dashboard,
            alerts_object_prefix: update_grafana_alerts,
        }

        for object_prefix, update_function in object_prefix_to_update_function.items():
            if object_key.startswith(object_prefix):
                update_function(
                    object_json=object_json,
                    object_key=object_key,
                    api_headers=api_headers,
                    grafana_workspace_endpoint=grafana_workspace_endpoint,
                )
                break


@tracer.capture_method
def update_grafana_dashboard(
    object_json: Dict[str, Any],
    object_key: str,
    api_headers: Dict[str, Any],
    grafana_workspace_endpoint: str,
) -> None:
    # update the dashboard using grafana http api
    response = requests.post(
        url=f"https://{grafana_workspace_endpoint}/api/dashboards/db",
        headers=api_headers,
        json=object_json,
        timeout=10,
    )
    if not response.ok:
        raise GrafanaApiError(response.text)

    logger.info(
        "Successfully updated the dashboard from the s3 file %s !",
        object_key,
        extra={"response": response.text},
    )


@tracer.capture_method
def update_grafana_alerts(
    object_json: Dict[str, Any],
    object_key: str,
    api_headers: Dict[str, Any],
    grafana_workspace_endpoint: str,
) -> None:
    alerts_object_prefix = os.environ["ALERTS_S3_OBJECT_KEY_PREFIX"]
    object_key = object_key.replace(alerts_object_prefix, "", 1)
    alerts_folder_name = object_key.split("/")[0]

    # create alert group folder for adding alert rules
    folder_response = requests.post(
        url=f"https://{grafana_workspace_endpoint}/api/folders",
        headers=api_headers,
        json={
            "title": alerts_folder_name,
        },
        timeout=10,
    )
    if not folder_response.ok:
        raise GrafanaApiError(folder_response.text)

    logger.info(
        "Successfully created folder for alerts!",
        extra={"response": folder_response.json()},
    )

    # create alert rules
    alert_rules_response = requests.post(
        url=f"https://{grafana_workspace_endpoint}/api/ruler/grafana/api/v1/rules/{alerts_folder_name}",
        headers=api_headers,
        json=object_json,
        timeout=10,
    )
    if not alert_rules_response.ok:
        raise GrafanaApiError(folder_response.text)

    logger.info(
        "Successfully created alert rules!",
        extra={"response": alert_rules_response.json()},
    )
