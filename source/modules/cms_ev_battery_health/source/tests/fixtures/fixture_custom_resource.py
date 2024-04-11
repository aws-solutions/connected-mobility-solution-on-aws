# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
from typing import Any, Dict, Generator, Tuple

# Third Party Libraries
import pytest
from mypy_boto3_secretsmanager.type_defs import CreateSecretResponseTypeDef

# Connected Mobility Solution on AWS
from ...handlers.custom_resource.function.lib.custom_resource_type_enum import (
    CustomResourceType,
)
from ...handlers.custom_resource.function.lib.data_sources import GrafanaDataSourceType


@pytest.fixture(name="custom_resource_event")
def fixture_custom_resource_event() -> Dict[str, Any]:
    return {
        "ResponseURL": "https://test-response-url.com",
        "StackId": "test-stack-id",
        "RequestId": "test-request-id",
        "ResourceType": "test-resource-type",
        "ResourceProperties": {},
        "LogicalResourceId": "test-logical-resource-id",
        "PhysicalResourceId": "test-physical-resource-id",
        "OldResourceProperties": {},
    }


@pytest.fixture(name="custom_resource_create_grafana_api_key_event")
def fixture_custom_resource_create_grafana_api_key_event(
    custom_resource_event: Dict[str, Any],
    grafana_api_key_secret: CreateSecretResponseTypeDef,
) -> Generator[Dict[str, Any], None, None]:
    custom_resource_event["RequestType"] = CustomResourceType.RequestType.CREATE.value
    custom_resource_event["ResourceProperties"] = {
        "Resource": CustomResourceType.ResourceType.CREATE_GRAFANA_API_KEY.value,
        "GrafanaWorkspaceId": "test-workspace-id",
        "GrafanaApiKeySecretArn": grafana_api_key_secret["ARN"],
        "GrafanaApiKeyExpirationDays": 30,
    }
    yield custom_resource_event


@pytest.fixture(name="custom_resource_install_grafana_plugin_event")
def fixture_custom_resource_install_grafana_plugin_event(
    custom_resource_event: Dict[str, Any],
    grafana_api_key_secret: CreateSecretResponseTypeDef,
) -> Generator[Dict[str, Any], None, None]:
    custom_resource_event["RequestType"] = CustomResourceType.RequestType.CREATE.value
    custom_resource_event["ResourceProperties"] = {
        "Resource": CustomResourceType.ResourceType.INSTALL_GRAFANA_PLUGIN.value,
        "GrafanaWorkspaceEndpoint": "test-endpoint.com",
        "GrafanaApiKeySecretArn": grafana_api_key_secret["ARN"],
        "PluginName": "test-plugin-name",
    }
    yield custom_resource_event


@pytest.fixture(name="custom_resource_create_grafana_data_source_event")
def fixture_custom_resource_create_grafana_data_source_event(
    custom_resource_event: Dict[str, Any],
    grafana_api_key_secret: CreateSecretResponseTypeDef,
) -> Generator[Dict[str, Any], None, None]:
    custom_resource_event["RequestType"] = CustomResourceType.RequestType.CREATE.value
    custom_resource_event["ResourceProperties"] = {
        "Resource": CustomResourceType.ResourceType.CREATE_GRAFANA_DATA_SOURCE.value,
        "DataSourceType": GrafanaDataSourceType.ATHENA.value,
        "GrafanaWorkspaceEndpoint": "test-endpoint.com",
        "GrafanaApiKeySecretArn": grafana_api_key_secret["ARN"],
        "DataSourceProperties": {
            "catalog": "test-catalog",
            "database": "test-database",
            "workgroup": "test-workgroup",
            "defaultRegion": "us-east-1",
        },
    }
    yield custom_resource_event


@pytest.fixture(name="custom_resource_create_grafana_dashboard_and_upload_to_s3_event")
def fixture_custom_resource_create_grafana_dashboard_and_upload_to_s3_event(
    custom_resource_event: Dict[str, Any],
    s3_dashboard_bucket: Tuple[str, str],
) -> Generator[Dict[str, Any], None, None]:
    custom_resource_event["RequestType"] = CustomResourceType.RequestType.CREATE.value
    custom_resource_event["ResourceProperties"] = {
        "Resource": CustomResourceType.ResourceType.CREATE_GRAFANA_DASHBOARD_AND_UPLOAD_TO_S3.value,
        "GrafanaS3Bucket": s3_dashboard_bucket,
        "DashboardS3ObjectKeyPrefix": os.environ["DASHBOARD_S3_OBJECT_KEY_PREFIX"],
        "DataSources": {
            GrafanaDataSourceType.ATHENA.value: {
                "data_source": {
                    "type": GrafanaDataSourceType.ATHENA.value,
                    "uid": "test-uid",
                },
                "athena_table": "test-athena-table",
            }
        },
    }
    yield custom_resource_event


@pytest.fixture(name="custom_resource_enable_grafana_alerting_event")
def fixture_custom_resource_enable_grafana_alerting_event(
    custom_resource_event: Dict[str, Any],
) -> Generator[Dict[str, Any], None, None]:
    custom_resource_event["RequestType"] = CustomResourceType.RequestType.CREATE.value
    custom_resource_event["ResourceProperties"] = {
        "Resource": CustomResourceType.ResourceType.ENABLE_GRAFANA_ALERTING.value,
        "GrafanaWorkspaceId": "test-workspace-id",
    }
    yield custom_resource_event


@pytest.fixture(name="custom_resource_set_grafana_alert_configuration_event")
def fixture_custom_resource_set_grafana_alert_configuration_event(
    custom_resource_event: Dict[str, Any],
    grafana_api_key_secret: CreateSecretResponseTypeDef,
) -> Generator[Dict[str, Any], None, None]:
    custom_resource_event["RequestType"] = CustomResourceType.RequestType.CREATE.value
    custom_resource_event["ResourceProperties"] = {
        "Resource": CustomResourceType.ResourceType.SET_GRAFANA_ALERT_CONFIGURATION.value,
        "GrafanaWorkspaceEndpoint": "test-workspace-endpoint",
        "GrafanaApiKeySecretArn": grafana_api_key_secret["ARN"],
        "GrafanaAlertsSnsTopicArn": "test-sns-topic-arn",
    }
    yield custom_resource_event


@pytest.fixture(name="custom_resource_create_grafana_alerts_and_upload_to_s3_event")
def fixture_custom_resource_create_grafana_alerts_and_upload_to_s3_event(
    custom_resource_event: Dict[str, Any],
    s3_dashboard_bucket: Tuple[str, str],
) -> Generator[Dict[str, Any], None, None]:
    custom_resource_event["RequestType"] = CustomResourceType.RequestType.CREATE.value
    custom_resource_event["ResourceProperties"] = {
        "Resource": CustomResourceType.ResourceType.CREATE_GRAFANA_ALERTS_AND_UPLOAD_TO_S3.value,
        "GrafanaS3Bucket": s3_dashboard_bucket,
        "AlertsS3ObjectKeyPrefix": os.environ["ALERTS_S3_OBJECT_KEY_PREFIX"],
        "DataSources": {
            GrafanaDataSourceType.ATHENA.value: {
                "data_source": {
                    "type": GrafanaDataSourceType.ATHENA.value,
                    "uid": "test-uid",
                },
                "athena_table": "test-athena-table",
            }
        },
    }
    yield custom_resource_event
