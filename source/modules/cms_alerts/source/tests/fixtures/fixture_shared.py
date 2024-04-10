# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
from typing import Dict, Generator, cast
from unittest.mock import patch

# Third Party Libraries
import pytest

# AWS Libraries
from aws_lambda_powertools.utilities.typing import LambdaContext


@pytest.fixture(name="context")
def fixture_context() -> LambdaContext:
    class MockLambdaContext:
        def __init__(self) -> None:
            self.function_name = "test"
            self.memory_limit_in_mb = 128
            self.invoked_function_arn = (
                "arn:aws:lambda:us-east-1:809313241:function:test"
            )
            self.aws_request_id = "52fdfc07-2182-154f-163f-5f0f9a621d72"
            self.log_stream_name = "TestLogStream"

    return cast(LambdaContext, MockLambdaContext())


# Prevents boto from accidentally using default AWS credentials if not mocked
@pytest.fixture(name="aws_credentials_env_vars", scope="session")
def fixture_aws_credentials_env_vars() -> Dict[str, str]:
    return {
        "AWS_ACCESS_KEY_ID": "testing",  # nosec
        "AWS_SECRET_ACCESS_ID": "testing",  # nosec
        "AWS_SECURITY_TOKEN": "testing",  # nosec
        "AWS_SESSION_TOKEN": "testing",  # nosec
        "AWS_SECRET_ACCESS_KEY": "testing",  # nosec
        "AWS_DEFAULT_REGION": "us-east-1",  # nosec
    }


@pytest.fixture(name="mock_module_env_vars", scope="session")
def fixture_mock_module_env_vars() -> Dict[str, str]:
    return {
        "APPLICATION_TYPE": "test-application-type",
        "SOLUTION_ID": "test-solution-id",
        "SOLUTION_NAME": "test-solution-name",
        "SOLUTION_VERSION": "v0.0.0",
        "S3_ASSET_BUCKET_BASE_NAME": "test-bucket-name",
        "S3_ASSET_KEY_PREFIX": "test-key-prefix",
        "USER_AGENT_STRING": "test-user-agent-string",
        "ALERTS_SNS_TOPIC_ARN": "test-topic-arn",
        "SNS_TOPIC_PREFIX": "test-topic-prefix",
        "NOTIFICATIONS_TABLE_NAME": "test-notifications-table-name",
        "USER_EMAIL_SUBSCRIPTIONS_TABLE": "test-user-email-subscriptions-table",
        "ALARM_TYPES": '{"alarm_types": ["TEST_ALARM1", "TEST_ALARM2"]}',
        "TOKEN_VALIDATION_LAMBDA_ARN": "test_token_validation_lambda_arn",
        "DEPLOYMENT_UUID": "test_deployment_uuid",
        "SNS_TOPIC_GENERAL_KEY_ID": "test-topic-key-id",
    }


@pytest.fixture(scope="session", autouse=True)
def fixture_mock_env_vars(
    aws_credentials_env_vars: Dict[str, str], mock_module_env_vars: Dict[str, str]
) -> Generator[None, None, None]:
    env_vars = {
        **aws_credentials_env_vars,
        **mock_module_env_vars,
    }
    with patch.dict(os.environ, env_vars):
        yield
