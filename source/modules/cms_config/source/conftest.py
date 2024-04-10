# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0


# pylint: disable=unused-import

# Standard Library
import os
from typing import Dict, Generator, cast
from unittest.mock import patch

# Third Party Libraries
import pytest

# AWS Libraries
from aws_lambda_powertools.utilities.typing import LambdaContext

# Connected Mobility Solution on AWS
from .handlers.aws_resource_lookup.function.tests.fixture_aws_resource_lookup_function import (
    fixture_aws_resource_lookup_event,
    fixture_aws_resource_lookup_event_identity_provider_id,
    fixture_mock_boto_identity_provider_id_ssm_parameter,
)
from .handlers.custom_resource.function.tests.fixture_custom_resource_function import (
    fixture_custom_resource_create_deployment_uuid_event,
    fixture_custom_resource_event,
)
from .handlers.metrics.function.lib.tests.fixture_metrics_function_lib import (
    get_halfway_yesterday_time_utc,
    get_solution_resource_tags,
)
from .infrastructure.tests.fixture_infrastructure import (
    fixture_snapshot_json_with_matcher,
)


# Prevents boto from accidentally using default AWS credentials if not mocked
@pytest.fixture(name="aws_credentials_env_vars", scope="module")
def fixture_aws_credentials_env_vars() -> Dict[str, str]:
    return {
        "AWS_ACCESS_KEY_ID": "testing",  # nosec
        "AWS_SECRET_ACCESS_ID": "testing",  # nosec
        "AWS_SECURITY_TOKEN": "testing",  # nosec
        "AWS_SESSION_TOKEN": "testing",  # nosec
        "AWS_SECRET_ACCESS_KEY": "testing",  # nosec
        "AWS_DEFAULT_REGION": "us-east-1",  # nosec
    }


@pytest.fixture(name="mock_module_env_vars", scope="module")
def fixture_mock_module_env_vars() -> Dict[str, str]:
    return {
        "APPLICATION_TYPE": "test-application-type",
        "SOLUTION_ID": "test-solution-id",
        "SOLUTION_NAME": "test-solution-name",
        "SOLUTION_VERSION": "v0.0.0",
        "S3_ASSET_BUCKET_BASE_NAME": "test-bucket-name",
        "S3_ASSET_KEY_PREFIX": "test-key-prefix",
        "USER_AGENT_STRING": "test-user-agent-string",
    }


@pytest.fixture(autouse=True)
def fixture_mock_env_vars(
    aws_credentials_env_vars: Dict[str, str], mock_module_env_vars: Dict[str, str]
) -> Generator[None, None, None]:
    env_vars = {
        **aws_credentials_env_vars,
        **mock_module_env_vars,
    }
    with patch.dict(os.environ, env_vars):
        yield


@pytest.fixture(name="context", scope="session")
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
