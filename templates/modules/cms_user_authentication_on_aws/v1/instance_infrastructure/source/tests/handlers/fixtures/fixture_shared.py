# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
from typing import Generator, cast
from unittest.mock import patch

# Third Party Libraries
import pytest
from aws_lambda_powertools.utilities.typing import LambdaContext

# Connected Mobility Solution on AWS
from ....config.constants import UserAuthenticationConstants
from ..token_exchange_lambda.test_token_exchange_lambda import (
    TokenExchangeAPICallBooleans,
)


@pytest.fixture(autouse=True, scope="session")
def mock_env_vars() -> Generator[None, None, None]:
    env_vars = os.environ.copy()
    env_vars.update(
        {
            "USER_AGENT_STRING": UserAuthenticationConstants.USER_AGENT_STRING,
            "COGNITO_USER_POOL_ID": "TestUserPoolId",
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


@pytest.fixture(name="reset_api_booleans", autouse=True)
def fixture_reset_api_booleans() -> None:
    TokenExchangeAPICallBooleans.reset_values()
