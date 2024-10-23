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
from cms_common.auth.auth_configs import CMSClientConfig, CMSIdPConfig
from cms_common.resource_names.auth import AuthSetupResourceNames

# Connected Mobility Solution on AWS
from ...handlers.process_alerts.function import main

MOCKED_TOKEN_ENDPOINT = "https://test-token-endpoint.com"  # nosec
TEST_IDENTITY_PROVIDER_ID = "test-identity-provider-id"
TEST_AUTH_SETUP_RESOURCE_NAMES_CLASS = AuthSetupResourceNames.from_identity_provider_id(
    TEST_IDENTITY_PROVIDER_ID
)


@pytest.fixture(autouse=True)
def fixture_process_alerts_clear_lru_caches() -> None:
    cached_functions: List[_lru_cache_wrapper[Any]] = [
        main.get_service_client_config_from_common,
        main.get_idp_config_from_common,
        main.get_access_token,
    ]
    for function in cached_functions:
        function.cache_clear()


@pytest.fixture(name="mock_process_alerts_environment_valid")
def fixture_mock_process_alerts_environment_valid() -> Generator[None, None, None]:
    env_vars = os.environ.copy()
    env_vars.update(
        {
            "USER_AGENT_STRING": "test-user-agent-string",
            "ALERTS_PUBLISH_ENDPOINT_URL": "https://test-alert-url.com",
            "IDENTITY_PROVIDER_ID": TEST_IDENTITY_PROVIDER_ID,
        }
    )
    with patch.dict(os.environ, env_vars):
        yield


@pytest.fixture(name="process_alerts_event", scope="session")
def fixture_process_alerts_event() -> Dict[str, Any]:
    return {
        "Records": [
            {
                "Sns": {
                    "Message": json.dumps(
                        {
                            "alerts": [
                                {
                                    "status": "firing",
                                    "labels": {
                                        "alertname": "test-alert-name",
                                        "vin": "test-vin",
                                    },
                                },
                                {
                                    "status": "resolved",
                                    "labels": {
                                        "alertname": "test-alert-name",
                                        "vin": "test-vin",
                                    },
                                },
                            ],
                        }
                    ),
                }
            }
        ],
    }


@pytest.fixture(name="auth_client_config_secret_string_valid", scope="session")
def fixture_auth_client_config_secret_string_valid() -> str:
    auth_client_config_json: CMSClientConfig = {
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
            Name=TEST_AUTH_SETUP_RESOURCE_NAMES_CLASS.service_client_config_secret,
            SecretString=auth_client_config_secret_string_valid,
        )["ARN"]

        ssm_client = boto3.client("ssm")
        ssm_client.put_parameter(
            Name=TEST_AUTH_SETUP_RESOURCE_NAMES_CLASS.service_client_config_secret_arn_ssm_parameter,
            Value=secret_arn,
            Type="String",
        )

        yield


@pytest.fixture(name="auth_idp_config_secret_string_valid", scope="session")
def fixture_auth_idp_config_secret_string_valid() -> str:
    auth_idp_config_json: CMSIdPConfig = {
        "issuer": "TEST_ISSUER",
        "token_endpoint": MOCKED_TOKEN_ENDPOINT,
        "authorization_endpoint": "TEST_AUTHORIZATION_ENDPOINT",
        "alternate_aud_key": "TEST_ALTERNATE_AUD_KEY",
        "auds": ["TEST_KNOWN_AUDS"],
        "scopes": ["TEST_KNOWN_SCOPES"],
    }
    return json.dumps(auth_idp_config_json)


@pytest.fixture(name="mock_boto_idp_config_valid")
def fixture_mock_boto_idp_config_valid(
    auth_idp_config_secret_string_valid: str,
) -> Generator[None, None, None]:
    with mock_aws():
        secretsmanager_client = boto3.client("secretsmanager")
        secret_arn = secretsmanager_client.create_secret(
            Name=TEST_AUTH_SETUP_RESOURCE_NAMES_CLASS.idp_config_secret,
            SecretString=auth_idp_config_secret_string_valid,
        )["ARN"]

        ssm_client = boto3.client("ssm")
        ssm_client.put_parameter(
            Name=TEST_AUTH_SETUP_RESOURCE_NAMES_CLASS.idp_config_secret_arn_ssm_parameter,
            Value=secret_arn,
            Type="String",
        )

        yield
