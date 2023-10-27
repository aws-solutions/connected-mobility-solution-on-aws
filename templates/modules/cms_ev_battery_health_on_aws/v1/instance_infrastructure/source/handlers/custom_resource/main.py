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
from .lib.alert_configs import ALERT_GROUP_CONFIGS
from .lib.alert_helpers import (
    convert_grafanalib_alert_group_to_json_str,
    create_alert_notification_policy_payload,
    create_sns_alert_contact_point_payload,
)
from .lib.custom_exceptions import GrafanaApiError
from .lib.custom_resource_type_enum import CustomResourceType
from .lib.dashboard_configs import DASHBOARD_CONFIGS
from .lib.dashboard_helpers import convert_grafanalib_dashboard_to_json_str
from .lib.data_sources import GrafanaDataSourceType, construct_athena_data_source

if TYPE_CHECKING:
    # Third Party Libraries
    from mypy_boto3_grafana.client import ManagedGrafanaClient
    from mypy_boto3_s3.client import S3Client
    from mypy_boto3_secretsmanager.client import SecretsManagerClient
else:
    SecretsManagerClient = object
    ManagedGrafanaClient = object
    S3Client = object


tracer = Tracer()
logger = Logger()


@lru_cache(maxsize=128)
def get_grafana_client() -> ManagedGrafanaClient:
    return boto3.client(
        "grafana", config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"])
    )


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
def handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    response = {"Status": CustomResourceType.StatusType.FAILED.value, "Data": {}}

    resource_map = {
        CustomResourceType.ResourceType.CREATE_GRAFANA_API_KEY.value: create_grafana_api_key,
        CustomResourceType.ResourceType.CREATE_GRAFANA_DATA_SOURCE.value: create_grafana_data_source,
        CustomResourceType.ResourceType.CREATE_GRAFANA_DASHBOARD_AND_UPLOAD_TO_S3.value: create_grafana_dashboard_and_upload_to_s3,
        CustomResourceType.ResourceType.ENABLE_GRAFANA_ALERTING.value: enable_grafana_alerting,
        CustomResourceType.ResourceType.SET_GRAFANA_ALERT_CONFIGURATION.value: set_grafana_alert_configuration,
        CustomResourceType.ResourceType.CREATE_GRAFANA_ALERTS_AND_UPLOAD_TO_S3.value: create_grafana_alerts_and_upload_to_s3,
    }

    try:
        response["Data"] = resource_map[event["ResourceProperties"]["Resource"]](event)  # type: ignore
        response["Status"] = CustomResourceType.StatusType.SUCCESS.value
    except Exception as exception:  # pylint: disable=W0703
        # Wrap all exceptions so CloudFormation doesn't hang
        logger.error("CustomResource error: %s", exception, exc_info=True)

    if bool(event["ResourceProperties"].get("DoNotSendCFResponse", False)) is not True:
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

    headers = {"Content-Type": "application/json"}

    requests.put(
        event["ResponseURL"],
        data=json.dumps(response_body),
        headers=headers,
        timeout=60,
    )


@tracer.capture_method
def create_grafana_api_key(event: Dict[str, Any]) -> None:
    if event["RequestType"] in [
        CustomResourceType.RequestType.CREATE.value,
        CustomResourceType.RequestType.UPDATE.value,
    ]:
        grafana_api_key_secret_arn = event["ResourceProperties"][
            "GrafanaApiKeySecretArn"
        ]
        grafana_workspace_id = event["ResourceProperties"]["GrafanaWorkspaceId"]
        api_key_expiration_days = int(
            event["ResourceProperties"]["GrafanaApiKeyExpirationDays"]
        )

        # create grafana api key with the desired expiration
        admin_api_key = get_grafana_client().create_workspace_api_key(
            keyName=str(uuid.uuid4()),
            keyRole="ADMIN",
            secondsToLive=api_key_expiration_days * 24 * 60 * 60,
            workspaceId=grafana_workspace_id,
        )
        logger.info(
            "Successfully created a grafana api key which expires in %d days.",
            api_key_expiration_days,
        )

        # put the api key in a secretsmanager secret
        get_secrets_manager_client().put_secret_value(
            SecretId=grafana_api_key_secret_arn,
            SecretString=json.dumps(admin_api_key),
            ClientRequestToken=str(uuid.uuid4()),
        )
        logger.info(
            "Successfully stored the grafana api key in a secret: %s",
            grafana_api_key_secret_arn,
        )


@tracer.capture_method
def create_grafana_data_source(event: Dict[str, Any]) -> Dict[str, Any]:
    data_source_response = {}
    if event["RequestType"] in [
        CustomResourceType.RequestType.CREATE.value,
        CustomResourceType.RequestType.UPDATE.value,
    ]:
        grafana_workspace_endpoint = event["ResourceProperties"][
            "GrafanaWorkspaceEndpoint"
        ]
        grafana_api_key_secret_arn = event["ResourceProperties"][
            "GrafanaApiKeySecretArn"
        ]
        data_source_type = event["ResourceProperties"]["DataSourceType"]
        data_source_properties = event["ResourceProperties"]["DataSourceProperties"]

        data_source = {}
        if data_source_type == GrafanaDataSourceType.ATHENA.value:
            data_source = construct_athena_data_source(
                properties=data_source_properties
            )

        api_key = json.loads(
            get_secrets_manager_client().get_secret_value(
                SecretId=grafana_api_key_secret_arn,
            )["SecretString"]
        )["key"]
        logger.info("Successfully retrived grafana api key from the secret.")

        response = requests.post(
            url=f"https://{grafana_workspace_endpoint}/api/datasources",
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
            json=data_source,
            timeout=10,
        )
        if not response.ok:
            raise GrafanaApiError(response.text)

        logger.info(
            "Successfully added data source!", extra={"response": response.json()}
        )
        data_source_response = response.json()

    return data_source_response


@tracer.capture_method
def create_grafana_dashboard_and_upload_to_s3(event: Dict[str, Any]) -> None:
    if event["RequestType"] in [
        CustomResourceType.RequestType.CREATE.value,
        CustomResourceType.RequestType.UPDATE.value,
    ]:
        dashboard_s3_bucket = event["ResourceProperties"]["GrafanaS3Bucket"]
        data_sources = event["ResourceProperties"]["DataSources"]

        for dashboard_config in DASHBOARD_CONFIGS:
            dashboard_s3_object_key = (
                event["ResourceProperties"]["DashboardS3ObjectKeyPrefix"]
                + dashboard_config.s3_object_key_name
            )
            dashboard = dashboard_config.dashboard_creator_func(data_sources)
            dashboard_json_str = convert_grafanalib_dashboard_to_json_str(
                dashboard=dashboard,
                overwrite=True,
                message=f"{dashboard_config.name} - updated at deployment",
            )

            # put the dashboard json file in the s3 bucket
            get_s3_client().put_object(
                Body=dashboard_json_str.encode("utf-8"),
                Bucket=dashboard_s3_bucket,
                Key=dashboard_s3_object_key,
            )
            logger.info(
                "Successfully put dashboard json in s3 bucket %s with key %s",
                dashboard_s3_bucket,
                dashboard_s3_object_key,
            )


@tracer.capture_method
def enable_grafana_alerting(event: Dict[str, Any]) -> None:
    if event["RequestType"] in [
        CustomResourceType.RequestType.CREATE.value,
        CustomResourceType.RequestType.UPDATE.value,
    ]:
        grafana_workspace_id = event["ResourceProperties"]["GrafanaWorkspaceId"]

        workspace_configuration = {"unifiedAlerting": {"enabled": True}}

        get_grafana_client().update_workspace_configuration(
            workspaceId=grafana_workspace_id,
            configuration=json.dumps(workspace_configuration),
        )
        logger.info(
            f"Enabled alerting in the Grafana workspace. New workspace configuration: {workspace_configuration}"
        )


@tracer.capture_method
def set_grafana_alert_configuration(event: Dict[str, Any]) -> None:
    if event["RequestType"] in [
        CustomResourceType.RequestType.CREATE.value,
        CustomResourceType.RequestType.UPDATE.value,
    ]:
        grafana_workspace_endpoint = event["ResourceProperties"][
            "GrafanaWorkspaceEndpoint"
        ]
        grafana_api_key_secret_arn = event["ResourceProperties"][
            "GrafanaApiKeySecretArn"
        ]
        grafana_alerts_sns_topic_arn = event["ResourceProperties"][
            "GrafanaAlertsSnsTopicArn"
        ]

        api_key = json.loads(
            get_secrets_manager_client().get_secret_value(
                SecretId=grafana_api_key_secret_arn,
            )["SecretString"]
        )["key"]
        logger.info("Successfully retrived grafana api key from the secret.")

        api_headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

        alert_contact_point_name = "grafana-alerts-ev-battery-health-on-aws-stack"

        # create alert contact point to be an sns topic
        contact_point_response = requests.post(
            url=f"https://{grafana_workspace_endpoint}/api/v1/provisioning/contact-points",
            headers=api_headers,
            json=create_sns_alert_contact_point_payload(
                name=alert_contact_point_name,
                topic_arn=grafana_alerts_sns_topic_arn,
            ),
            timeout=10,
        )
        if not contact_point_response.ok:
            raise GrafanaApiError(contact_point_response.text)

        logger.info(
            "Successfully added alert contact point!",
            extra={"response": contact_point_response.json()},
        )

        # create alert notification policy for the configured alert points
        notification_policy_response = requests.put(
            url=f"https://{grafana_workspace_endpoint}/api/v1/provisioning/policies",
            headers=api_headers,
            json=create_alert_notification_policy_payload(
                receiver=alert_contact_point_name,
            ),
            timeout=10,
        )
        if not notification_policy_response.ok:
            raise GrafanaApiError(notification_policy_response.text)

        logger.info(
            "Successfully added alert notification policy!",
            extra={"response": notification_policy_response.json()},
        )


@tracer.capture_method
def create_grafana_alerts_and_upload_to_s3(event: Dict[str, Any]) -> None:
    if event["RequestType"] in [
        CustomResourceType.RequestType.CREATE.value,
        CustomResourceType.RequestType.UPDATE.value,
    ]:
        alerts_s3_bucket = event["ResourceProperties"]["GrafanaS3Bucket"]
        data_sources = event["ResourceProperties"]["DataSources"]

        for alert_group_config in ALERT_GROUP_CONFIGS:
            alerts_s3_object_key = (
                f'{event["ResourceProperties"]["AlertsS3ObjectKeyPrefix"]}'
                f"{alert_group_config.alert_group_folder}/"
                f"{alert_group_config.s3_object_key_name}"
            )
            alert_rules_json_str = convert_grafanalib_alert_group_to_json_str(
                alert_group_config.alert_group_creator_func(data_sources)
            )

            # put the alert rules json file in the s3 bucket
            get_s3_client().put_object(
                Body=alert_rules_json_str.encode("utf-8"),
                Bucket=alerts_s3_bucket,
                Key=alerts_s3_object_key,
            )
            logger.info(
                "Successfully put alert rules json in s3 bucket %s with key %s",
                alerts_s3_bucket,
                alerts_s3_object_key,
            )
