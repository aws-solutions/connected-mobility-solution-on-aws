# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json
import os
from functools import _lru_cache_wrapper
from typing import Any, Dict, Generator, List
from unittest.mock import patch

# Third Party Libraries
import pytest
from moto import mock_aws

# AWS Libraries
import boto3

# CMS Common Library
from cms_common.resource_names.auth import AuthResourceNames

# Connected Mobility Solution on AWS
from ....handlers.vehicle_trigger_alarm.function import main

MOCKED_ALERTS_PUBLISH_URL = "https://test-alert-url.com"
MOCKED_TOKEN_ENDPOINT = "https://test-token-endpoint.com"  # nosec
TEST_IDENTITY_PROVIDER_ID = "test-identity-provider-id"
TEST_AUTH_RESOURCE_NAMES_CLASS = AuthResourceNames.from_identity_provider_id(
    TEST_IDENTITY_PROVIDER_ID
)


@pytest.fixture(autouse=True)
def fixture_vehicle_trigger_alarm_clear_lru_caches() -> None:
    cached_functions: List[_lru_cache_wrapper[Any]] = [
        main.get_client_config_from_common,
        main.get_access_token,
    ]
    for function in cached_functions:
        function.cache_clear()


@pytest.fixture(name="mock_vehicle_trigger_alarm_environment_valid")
def fixture_vehicle_trigger_alarm_environment_valid() -> Generator[None, None, None]:
    env_vars = os.environ.copy()
    env_vars.update(
        {
            "ALERTS_PUBLISH_ENDPOINT_URL_PARAMETER": "/mocked/alerts_url",
            "USER_AGENT_STRING": "test-user-agent",
            "IDENTITY_PROVIDER_ID": TEST_IDENTITY_PROVIDER_ID,
        }
    )
    with patch.dict(os.environ, env_vars):
        yield


@pytest.fixture(name="vehicle_trigger_alarm_event", scope="module")
def fixture_vehicle_trigger_alarm_event() -> Dict[str, Any]:
    return {
        "vin": "test",
        "message": "test alert",
        "ResourceType": "TestResourceType",
        "LogicalResourceId": "TestLogicalResourceId",
        "PhysicalResourceId": "TestPysicalResourceId",
        "ResourceProperties": {},
        "OldResourceProperties": {},
    }


@pytest.fixture(name="auth_client_config_secret_string_valid", scope="module")
def fixture_auth_client_config_secret_string_valid() -> str:
    auth_client_config_json: dict[str, str] = {
        "token_endpoint": MOCKED_TOKEN_ENDPOINT,
        "client_id": "test-client-id",
        "client_secret": "test-client-secret",
        "audience": "test-audience",
    }
    return json.dumps(auth_client_config_json)


@pytest.fixture(name="mock_boto_client_config_valid")
def fixture_mock_boto_client_config_valid(
    auth_client_config_secret_string_valid: str,
) -> Generator[None, None, None]:
    with mock_aws():
        secretsmanager_client = boto3.client("secretsmanager")
        secret_arn = secretsmanager_client.create_secret(
            Name=TEST_AUTH_RESOURCE_NAMES_CLASS.client_config_secret,
            SecretString=auth_client_config_secret_string_valid,
        )["ARN"]

        ssm_client = boto3.client("ssm")
        ssm_client.put_parameter(
            Name=os.environ["ALERTS_PUBLISH_ENDPOINT_URL_PARAMETER"],
            Value=MOCKED_ALERTS_PUBLISH_URL,
            Type="String",
        )
        ssm_client.put_parameter(
            Name=TEST_AUTH_RESOURCE_NAMES_CLASS.client_config_secret_arn_ssm_parameter,
            Value=secret_arn,
            Type="String",
        )

        yield
