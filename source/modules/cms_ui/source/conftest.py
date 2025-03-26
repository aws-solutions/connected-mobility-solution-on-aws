# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# pylint: disable=unused-import

# Standard Library
from typing import cast

# Third Party Libraries
import pytest

# AWS Libraries
from aws_lambda_powertools.utilities.typing import LambdaContext

# Connected Mobility Solution on AWS
from .handlers.authorization.function.tests.fixture_authorization_function import (
    fixture_authorization_allow_policy,
    fixture_authorization_deny_policy,
    fixture_invalid_authorization_event,
    fixture_reset_api_booleans,
    fixture_valid_authorization_event,
    mock_env_for_authorization,
)
from .handlers.custom_resource.function.tests.fixture_custom_resource_function import (
    fixture_custom_resource_event,
)
from .tests.fixtures.fixture_boto3 import (
    fixture_mock_boto3_client,
    fixture_ssm_stubber,
    fixture_timestream_stubber,
)
from .tests.fixtures.fixture_shared import (
    fixture_aws_credentials_env_vars,
    fixture_mock_env_vars,
    fixture_mock_module_env_vars,
)
from .tests.infrastructure.fixtures.fixture_stack_templates import (
    fixture_cms_ui_stack_template,
    fixture_snapshot_json_with_matcher,
)


@pytest.fixture(name="context")
def fixture_context() -> LambdaContext:
    class MockLambdaContext:
        def __init__(self) -> None:
            self.function_name = "test"
            self.memory_limit_in_mb = 128
            self.invoked_function_arn = (
                "arn:aws:lambda:us-east-1:11111111111:function:test"
            )
            self.aws_request_id = "52fdfc07-2182-154f-163f-5f0f9a621d72"
            self.log_stream_name = "TestLogStream"

    return cast(LambdaContext, MockLambdaContext())
