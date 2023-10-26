# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0


# Standard Library
import json
from typing import Dict, Generator, cast

# Third Party Libraries
import boto3
import pytest
from aws_lambda_powertools.utilities.typing import LambdaContext
from moto import mock_secretsmanager  # type: ignore
from mypy_boto3_secretsmanager.type_defs import CreateSecretResponseTypeDef


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


# Prevents boto from accidentally using default AWS credentials if not mocked
@pytest.fixture(name="aws_credentials_env_vars", scope="session")
def fixture_aws_credentials_env_vars() -> Dict[str, str]:
    return {
        "AWS_ACCESS_KEY_ID": "testing",  # nosec
        "AWS_SECRET_ACCESS_ID": "testing",  # nosec
        "AWS_SECURITY_TOKEN": "testing",  # nosec"
        "AWS_SESSION_TOKEN": "testing",  # nosec
        "AWS_SECRET_ACCESS_KEY": "testing",  # nosec
        "AWS_DEFAULT_REGION": "us-east-1",  # nosec
    }


@pytest.fixture(name="service_client_credentials_secret")
def fixture_service_client_credentials_secret() -> (
    Generator[CreateSecretResponseTypeDef, None, None]
):
    with mock_secretsmanager():
        secretsmanager_client = boto3.client("secretsmanager")

        client_credentials = {
            "client_id": "test-client-id",
            "client_secret": "test-client-secret",
            "scope": "test-scope",
        }

        secret = secretsmanager_client.create_secret(
            Name="test-client-credentials-secret",
            ClientRequestToken="test-client-request-token-123456",
            SecretString=json.dumps(client_credentials),
        )

        yield secret
