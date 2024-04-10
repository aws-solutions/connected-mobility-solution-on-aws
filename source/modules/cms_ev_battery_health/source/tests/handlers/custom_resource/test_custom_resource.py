# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0


# Standard Library
# mypy: disable-error-code=misc
import json
from typing import Any, Dict
from unittest.mock import MagicMock, patch

# Third Party Libraries
import pytest
from mypy_boto3_secretsmanager.type_defs import CreateSecretResponseTypeDef

# AWS Libraries
import boto3
import botocore
from aws_lambda_powertools.utilities.typing import LambdaContext

# Connected Mobility Solution on AWS
from ....handlers.custom_resource.function.lib.alert_configs import ALERT_GROUP_CONFIGS
from ....handlers.custom_resource.function.lib.custom_exceptions import GrafanaApiError
from ....handlers.custom_resource.function.lib.custom_resource_type_enum import (
    CustomResourceType,
)
from ....handlers.custom_resource.function.lib.dashboard_configs import (
    DASHBOARD_CONFIGS,
)
from ....handlers.custom_resource.function.main import (
    create_grafana_alerts_and_upload_to_s3,
    create_grafana_api_key,
    create_grafana_dashboard_and_upload_to_s3,
    create_grafana_data_source,
    enable_grafana_alerting,
    handler,
    install_grafana_plugin,
    send_cloud_formation_response,
    set_grafana_alert_configuration,
)


# Flags to assert that an API call happened
class CustomResourceAPICallBooleans:
    CreateWorkspaceApiKey = False
    DeleteWorkspaceApiKey = False
    UpdateWorkspaceConfiguration = False

    @classmethod
    def reset_values(cls) -> None:
        for var in vars(CustomResourceAPICallBooleans):
            if not callable(
                getattr(CustomResourceAPICallBooleans, var)
            ) and not var.startswith("__"):
                setattr(CustomResourceAPICallBooleans, var, False)

    @classmethod
    def are_all_values_false(cls) -> bool:
        are_all_values_false = True
        for var in vars(CustomResourceAPICallBooleans):
            if not callable(
                getattr(CustomResourceAPICallBooleans, var)
            ) and not var.startswith("__"):
                if getattr(CustomResourceAPICallBooleans, var):
                    are_all_values_false = False
                    break
        return are_all_values_false


# pylint: disable=protected-access
orig = botocore.client.BaseClient._make_api_call  # type: ignore
# pylint: disable=too-many-return-statements, inconsistent-return-statements
def mock_make_api_call(self: Any, operation_name: str, kwarg: Any) -> Any:
    setattr(CustomResourceAPICallBooleans, operation_name, True)
    mock_api_responses = {
        "CreateWorkspaceApiKey": {
            "key": "test-grafana-api-key",
            "workspaceId": "test-grafana-workspace-id",
        },
        "DeleteWorkspaceApiKey": None,
        "UpdateWorkspaceConfiguration": None,
    }
    if operation_name in mock_api_responses:
        return mock_api_responses[operation_name]
    return orig(self, operation_name, kwarg)


def test_handler(
    custom_resource_create_grafana_api_key_event: Dict[str, Any],
    context: LambdaContext,
    mocker: MagicMock,
) -> None:
    mocked_requests: MagicMock = mocker.patch("requests.put")
    with patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call):
        response = handler(
            event=custom_resource_create_grafana_api_key_event, context=context
        )

    mocked_requests.assert_called_once()
    assert response["Status"] == CustomResourceType.StatusType.SUCCESS.value


def test_handler_invalid_event(
    custom_resource_event: Dict[str, Any],
    context: LambdaContext,
    mocker: MagicMock,
) -> None:
    mocked_requests: MagicMock = mocker.patch("requests.put")
    response = handler(custom_resource_event, context)

    mocked_requests.assert_called_once()
    assert response["Status"] == CustomResourceType.StatusType.FAILED.value


def test_send_cloud_formation_response(
    custom_resource_event: Dict[str, Any], mocker: MagicMock
) -> None:
    mocked_requests: MagicMock = mocker.patch("requests.put")

    input_response = {
        "Status": "SUCCESS",
        "Data": None,
    }
    reason = "test-reason"

    expected_response = json.dumps(
        {
            "Status": input_response["Status"],
            "Reason": reason,
            "PhysicalResourceId": custom_resource_event["LogicalResourceId"],
            "StackId": custom_resource_event["StackId"],
            "RequestId": custom_resource_event["RequestId"],
            "LogicalResourceId": custom_resource_event["LogicalResourceId"],
            "Data": input_response["Data"],
        }
    )
    headers = {"Content-Type": "application/json"}

    send_cloud_formation_response(custom_resource_event, input_response, reason)

    mocked_requests.assert_called_with(
        custom_resource_event["ResponseURL"],
        data=expected_response,
        headers=headers,
        timeout=60,
    )


def test_create_grafana_api_key(
    custom_resource_create_grafana_api_key_event: Dict[str, Any],
    grafana_api_key_secret: CreateSecretResponseTypeDef,
) -> None:
    with patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call):
        create_grafana_api_key(event=custom_resource_create_grafana_api_key_event)

    secretsmanager_client = boto3.client("secretsmanager")
    api_key_secret = json.loads(
        secretsmanager_client.get_secret_value(
            SecretId=grafana_api_key_secret["ARN"],
        )["SecretString"]
    )

    assert isinstance(api_key_secret["key"], str)
    assert isinstance(api_key_secret["workspaceId"], str)


def test_install_grafana_plugin_success(
    custom_resource_install_grafana_plugin_event: Dict[str, Any],
    mocker: MagicMock,
) -> None:
    mocked_requests: MagicMock = mocker.patch("requests.post")
    mocked_requests.return_value.ok = True

    with patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call):
        install_grafana_plugin(event=custom_resource_install_grafana_plugin_event)

    mocked_requests.assert_called_once()


def test_install_grafana_plugin_fail(
    custom_resource_install_grafana_plugin_event: Dict[str, Any],
    mocker: MagicMock,
) -> None:
    mocked_requests: MagicMock = mocker.patch("requests.post")
    mocked_requests.return_value.ok = False
    mocked_requests.return_value.status_code = 400

    with patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call):
        with pytest.raises(GrafanaApiError):
            install_grafana_plugin(event=custom_resource_install_grafana_plugin_event)

    mocked_requests.assert_called_once()


def test_create_grafana_data_source_success(
    custom_resource_create_grafana_data_source_event: Dict[str, Any],
    mocker: MagicMock,
) -> None:
    mocked_requests: MagicMock = mocker.patch("requests.post")
    mocked_requests.return_value.ok = True

    with patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call):
        create_grafana_data_source(
            event=custom_resource_create_grafana_data_source_event
        )

    mocked_requests.assert_called_once()


def test_create_grafana_data_source_fail(
    custom_resource_create_grafana_data_source_event: Dict[str, Any],
    mocker: MagicMock,
) -> None:
    mocked_requests: MagicMock = mocker.patch("requests.post")
    mocked_requests.return_value.ok = False

    with patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call):
        with pytest.raises(GrafanaApiError):
            create_grafana_data_source(
                event=custom_resource_create_grafana_data_source_event
            )

    mocked_requests.assert_called_once()


def test_create_grafana_dashboard_and_upload_to_s3(
    custom_resource_create_grafana_dashboard_and_upload_to_s3_event: Dict[str, Any],
) -> None:
    create_grafana_dashboard_and_upload_to_s3(
        event=custom_resource_create_grafana_dashboard_and_upload_to_s3_event
    )

    s3_client = boto3.client("s3")
    s3_bucket = custom_resource_create_grafana_dashboard_and_upload_to_s3_event[
        "ResourceProperties"
    ]["GrafanaS3Bucket"]
    s3_object_prefix = custom_resource_create_grafana_dashboard_and_upload_to_s3_event[
        "ResourceProperties"
    ]["DashboardS3ObjectKeyPrefix"]
    for dashboard_config in DASHBOARD_CONFIGS:
        dashboard_obj = s3_client.get_object(
            Bucket=s3_bucket,
            Key=f"{s3_object_prefix}{dashboard_config.s3_object_key_name}",
        )
        assert dashboard_obj["Body"] is not None


def test_enable_grafana_alerting(
    custom_resource_enable_grafana_alerting_event: Dict[str, Any]
) -> None:
    with patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call):
        enable_grafana_alerting(event=custom_resource_enable_grafana_alerting_event)
    assert CustomResourceAPICallBooleans.UpdateWorkspaceConfiguration is True


@pytest.mark.parametrize(
    "post_result,put_result",
    [(True, True), (True, False), (False, True), (False, False)],
)
def test_set_grafana_alert_configuration(
    custom_resource_set_grafana_alert_configuration_event: Dict[str, Any],
    mocker: MagicMock,
    post_result: bool,
    put_result: bool,
) -> None:
    mocked_post_requests: MagicMock = mocker.patch("requests.post")
    mocked_post_requests.return_value.ok = post_result

    mocked_put_requests: MagicMock = mocker.patch("requests.put")
    mocked_put_requests.return_value.ok = put_result

    if post_result and put_result:
        set_grafana_alert_configuration(
            event=custom_resource_set_grafana_alert_configuration_event
        )
    else:
        with pytest.raises(GrafanaApiError):
            set_grafana_alert_configuration(
                event=custom_resource_set_grafana_alert_configuration_event
            )

    if post_result:
        mocked_post_requests.assert_called_once()
        mocked_put_requests.assert_called_once()
    else:
        mocked_post_requests.assert_called_once()


def test_create_grafana_alerts_and_upload_to_s3(
    custom_resource_create_grafana_alerts_and_upload_to_s3_event: Dict[str, Any],
) -> None:
    create_grafana_alerts_and_upload_to_s3(
        event=custom_resource_create_grafana_alerts_and_upload_to_s3_event
    )

    s3_client = boto3.client("s3")
    s3_bucket = custom_resource_create_grafana_alerts_and_upload_to_s3_event[
        "ResourceProperties"
    ]["GrafanaS3Bucket"]
    s3_object_prefix = custom_resource_create_grafana_alerts_and_upload_to_s3_event[
        "ResourceProperties"
    ]["AlertsS3ObjectKeyPrefix"]
    for alerts_config in ALERT_GROUP_CONFIGS:
        alerts_obj = s3_client.get_object(
            Bucket=s3_bucket,
            Key=f"{s3_object_prefix}{alerts_config.alert_group_folder}/{alerts_config.s3_object_key_name}",
        )
        assert alerts_obj["Body"] is not None
