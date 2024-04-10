# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
# mypy: disable-error-code="name-defined"

# Standard Library
import json
from typing import TYPE_CHECKING, Callable, Dict, List

# Third Party Libraries
import pytest
from moto import mock_aws

# AWS Libraries
import boto3

# Connected Mobility Solution on AWS
from ...resource_names.auth import AuthResourceNames

TEST_USER_AGENT_STRING = "test-user-agent-string"
TEST_IDENTITY_PROVIDER_ID = "test_idp"
TEST_AUTH_RESOURCE_NAMES_CLASS = AuthResourceNames.from_identity_provider_id(
    TEST_IDENTITY_PROVIDER_ID
)

if TYPE_CHECKING:
    # Third Party Libraries
    from mypy_boto3_secretsmanager import SecretsManagerClient
    from mypy_boto3_ssm import SSMClient
else:
    SecretsManagerClient = object
    SSMClient = object

# IDP CONFIG
@pytest.fixture(name="idp_config_secret_string_valid", scope="module")
def fixture_idp_config_secret_string_valid() -> Dict[str, str | List[str]]:
    idp_config_json: Dict[str, str | List[str]] = {
        "iss_domain": "TEST_ISS_DOMAIN",
        "alternate_aud_key": "TEST_ALTERNATE_AUD_KEY",
        "auds": [
            "TEST_USER_CLIENT_ID",
            "TEST_SERVICE_CLIENT_ID",
        ],
        "scopes": ["TEST_USER_SCOPE", "TEST_SERVICE_SCOPE"],
    }
    return idp_config_json


@pytest.fixture(name="mock_idp_config_valid")
def fixture_mock_idp_config_valid(
    idp_config_secret_string_valid: str,
) -> Callable[[], None]:
    @mock_aws
    def moto_boto() -> None:
        secretsmanager_client: SecretsManagerClient = boto3.client("secretsmanager")
        secret_arn = secretsmanager_client.create_secret(
            Name=TEST_AUTH_RESOURCE_NAMES_CLASS.idp_config_secret,
            SecretString=json.dumps(idp_config_secret_string_valid),
        )["ARN"]

        ssm_client: SSMClient = boto3.client("ssm")
        ssm_client.put_parameter(
            Name=TEST_AUTH_RESOURCE_NAMES_CLASS.idp_config_secret_arn_ssm_parameter,
            Value=secret_arn,
            Type="String",
        )

    return moto_boto


@pytest.fixture(name="mock_idp_config_invalid_json")
def fixture_mock_idp_config_invalid_json() -> Callable[[], None]:
    @mock_aws
    def moto_boto() -> None:
        secretsmanager_client: SecretsManagerClient = boto3.client("secretsmanager")
        secret_arn = secretsmanager_client.create_secret(
            Name=TEST_AUTH_RESOURCE_NAMES_CLASS.idp_config_secret,
            SecretString="Not a valid json string",
        )["ARN"]

        ssm_client: SSMClient = boto3.client("ssm")
        ssm_client.put_parameter(
            Name=TEST_AUTH_RESOURCE_NAMES_CLASS.idp_config_secret_arn_ssm_parameter,
            Value=secret_arn,
            Type="String",
        )

    return moto_boto


@pytest.fixture(name="mock_idp_config_invalid_data_format")
def fixture_mock_idp_config_invalid_data_format() -> Callable[[], None]:
    @mock_aws
    def moto_boto() -> None:
        secretsmanager_client: SecretsManagerClient = boto3.client("secretsmanager")
        secret_arn = secretsmanager_client.create_secret(
            Name=TEST_AUTH_RESOURCE_NAMES_CLASS.idp_config_secret,
            SecretString=json.dumps({"incorrect_key": "value"}),
        )["ARN"]

        ssm_client: SSMClient = boto3.client("ssm")
        ssm_client.put_parameter(
            Name=TEST_AUTH_RESOURCE_NAMES_CLASS.idp_config_secret_arn_ssm_parameter,
            Value=secret_arn,
            Type="String",
        )

    return moto_boto


# CLIENT CONFIG
@pytest.fixture(name="client_config_secret_string_valid", scope="module")
def fixture_client_config_secret_string_valid() -> dict[str, str]:
    client_config_json: dict[str, str] = {
        "audience": "",
        "token_endpoint": "TEST_TOKEN_ENDPOINT",
        "client_id": "TEST_CLIENT_ID",
        "client_secret": "TEST_CLIENT_SECRET",
    }
    return client_config_json


@pytest.fixture(name="mock_client_config_valid")
def fixture_mock_client_config_valid(
    client_config_secret_string_valid: str,
) -> Callable[[], None]:
    @mock_aws
    def moto_boto() -> None:
        secretsmanager_client: SecretsManagerClient = boto3.client("secretsmanager")
        secret_arn = secretsmanager_client.create_secret(
            Name=TEST_AUTH_RESOURCE_NAMES_CLASS.client_config_secret,
            SecretString=json.dumps(client_config_secret_string_valid),
        )["ARN"]

        ssm_client: SSMClient = boto3.client("ssm")
        ssm_client.put_parameter(
            Name=TEST_AUTH_RESOURCE_NAMES_CLASS.client_config_secret_arn_ssm_parameter,
            Value=secret_arn,
            Type="String",
        )

    return moto_boto


# AUTHORIZATION CODE FLOW CONFIG
@pytest.fixture(
    name="authorization_code_flow_config_secret_string_valid", scope="module"
)
def fixture_authorization_code_flow_config_secret_string_valid() -> dict[str, str]:
    client_config_json: dict[str, str] = {
        "token_endpoint": "TEST_TOKEN_ENDPOINT",
        "client_id": "TEST_CLIENT_ID",
        "client_secret": "TEST_CLIENT_SECRET",
    }
    return client_config_json


@pytest.fixture(name="mock_authorization_code_flow_config_valid")
def fixture_mock_authorization_code_flow_config_valid(
    authorization_code_flow_config_secret_string_valid: str,
) -> Callable[[], None]:
    @mock_aws
    def moto_boto() -> None:
        secretsmanager_client: SecretsManagerClient = boto3.client("secretsmanager")
        secret_arn = secretsmanager_client.create_secret(
            Name=TEST_AUTH_RESOURCE_NAMES_CLASS.authorization_code_flow_config_secret,
            SecretString=json.dumps(authorization_code_flow_config_secret_string_valid),
        )["ARN"]

        ssm_client: SSMClient = boto3.client("ssm")
        ssm_client.put_parameter(
            Name=TEST_AUTH_RESOURCE_NAMES_CLASS.authorization_code_flow_config_secret_arn_ssm_parameter,
            Value=secret_arn,
            Type="String",
        )

    return moto_boto
