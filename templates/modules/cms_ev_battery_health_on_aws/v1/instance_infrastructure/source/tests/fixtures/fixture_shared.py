# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json
import os
from typing import Any, Dict, Generator, cast
from unittest.mock import patch

# Third Party Libraries
import boto3
import pytest
from aws_lambda_powertools.utilities.typing import LambdaContext
from moto import mock_aws  # type: ignore
from mypy_boto3_secretsmanager.type_defs import CreateSecretResponseTypeDef

# Connected Mobility Solution on AWS
from ...config.constants import EVBatteryHealthConstants
from ..handlers.check_workspace_active.test_check_workspace_active import (
    CheckWorkspaceStatusAPICallBooleans,
)
from ..handlers.custom_resource.test_custom_resource import (
    CustomResourceAPICallBooleans,
)
from ..handlers.rotate_secret.test_rotate_secret import RotateSecretAPICallBooleans


@pytest.fixture(name="reset_api_booleans", autouse=True)
def fixture_reset_api_booleans() -> None:
    RotateSecretAPICallBooleans.reset_values()
    CustomResourceAPICallBooleans.reset_values()
    CheckWorkspaceStatusAPICallBooleans.reset_values()


@pytest.fixture(name="grafana_api_key_secret_metadata")
def fixture_grafana_api_key_secret_metadata() -> Dict[str, Any]:
    return {
        "SecretName": "test-secret-name",
        "CurrentVersion": "test-current-secret-token-123456",  # min length of token should be 32
        "PendingVersion": "test-pending-secret-token-123456",
    }


@pytest.fixture(name="grafana_api_key_secret")
def fixture_grafana_api_key_secret(
    grafana_api_key_secret_metadata: Dict[str, Any],
) -> Generator[CreateSecretResponseTypeDef, None, None]:
    with mock_aws():
        secretsmanager_client = boto3.client("secretsmanager")

        grafana_api_key = {
            "key": "test-grafana-api-key",
            "keyName": "test-grafana-api-key-name",
            "workspaceId": "test-grafana-workspace-id",
        }

        secret = secretsmanager_client.create_secret(
            Name=grafana_api_key_secret_metadata["SecretName"],
            ClientRequestToken=grafana_api_key_secret_metadata["CurrentVersion"],
            SecretString=json.dumps(grafana_api_key),
        )

        yield secret


@pytest.fixture(name="service_client_credentials_secret")
def fixture_service_client_credentials_secret() -> (
    Generator[CreateSecretResponseTypeDef, None, None]
):
    with mock_aws():
        secretsmanager_client = boto3.client("secretsmanager")

        secret = secretsmanager_client.create_secret(
            Name="test-client-credentials-secret",
            ClientRequestToken="test-client-request-token-123456",
            SecretString="test-secret",
        )

        yield secret


@pytest.fixture(name="s3_dashboard_bucket")
def fixture_s3_dashboard_bucket() -> Generator[str, None, None]:
    with mock_aws():
        s3_client = boto3.client("s3")

        dashboard_bucket_name = "test-dashboard-bucket"

        s3_client.create_bucket(
            Bucket=dashboard_bucket_name,
            CreateBucketConfiguration={"LocationConstraint": "ca-central-1"},
        )

        yield dashboard_bucket_name


# Prevents boto from accidentally using default AWS credentials if not mocked
@pytest.fixture(autouse=True, scope="session")
def fixture_aws_credentials_env_vars() -> None:
    os.environ.update(
        {
            "AWS_ACCESS_KEY_ID": "testing",  # nosec
            "AWS_SECRET_ACCESS_ID": "testing",  # nosec
            "AWS_SECURITY_TOKEN": "testing",  # nosec"
            "AWS_SESSION_TOKEN": "testing",  # nosec
            "AWS_SECRET_ACCESS_KEY": "testing",  # nosec
            "AWS_DEFAULT_REGION": "us-east-1",  # nosec
        }
    )


@pytest.fixture(autouse=True)
def mock_env_vars(
    grafana_api_key_secret: CreateSecretResponseTypeDef,
) -> Generator[None, None, None]:
    env_vars = os.environ.copy()
    env_vars.update(
        {
            "USER_AGENT_STRING": EVBatteryHealthConstants.USER_AGENT_STRING,
            "GRAFANA_WORKSPACE_ID": "mock-grafana-workspace-id",
            "GRAFANA_WORKSPACE_ENDPOINT": "mock-grafana-endpoint.com",
            "GRAFANA_API_KEY_SECRET_ARN": grafana_api_key_secret["ARN"],
            "GRAFANA_API_KEY_EXPIRATION_DAYS": str(
                EVBatteryHealthConstants.GRAFANA_API_KEY_EXPIRATION_DAYS
            ),
            "DASHBOARD_S3_OBJECT_KEY_PREFIX": EVBatteryHealthConstants.DASHBOARD_S3_OBJECT_KEY_PREFIX,
            "ALERTS_S3_OBJECT_KEY_PREFIX": EVBatteryHealthConstants.ALERTS_S3_OBJECT_KEY_PREFIX,
        }
    )

    with patch.dict(os.environ, env_vars):
        yield


@pytest.fixture(name="context")
def fixture_context() -> LambdaContext:
    class MockLambdaContext:
        def __init__(self) -> None:
            self.function_name = "test"
            self.memory_limit_in_mb = 128
            self.invoked_function_arn = (
                "arn:aws:lambda:eu-west-1:809313241:function:test"
            )
            self.aws_request_id = "52fdfc07-2182-154f-163f-5f0f9a621d72"
            self.log_stream_name = "TestLogSteam"

    return cast(LambdaContext, MockLambdaContext())
