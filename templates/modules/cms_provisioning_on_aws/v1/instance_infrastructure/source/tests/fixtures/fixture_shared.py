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
from ...config.constants import VPConstants
from ...handlers.provisioning.lib.dynamo_table_name_key_enum import DynamoTableNameKey
from ...tests.handlers.custom_resource.test_custom_resource import (
    CustomResourceAPICallBooleans,
)
from ...tests.handlers.provisioning.test_post_provision import (
    PostProvisioningAPICallBooleans,
)
from ...tests.handlers.provisioning.test_pre_provision import (
    PreProvisioningAPICallBooleans,
)


@pytest.fixture(name="reset_api_booleans", autouse=True)
def fixture_reset_api_booleans() -> None:
    PreProvisioningAPICallBooleans.reset_values()
    PostProvisioningAPICallBooleans.reset_values()
    CustomResourceAPICallBooleans.reset_values()


@pytest.fixture(autouse=True, scope="session")
def mock_env_vars() -> Generator[None, None, None]:
    env_vars = {
        DynamoTableNameKey.AUTHORIZED_VEHICLES_TABLE_NAME.value: "MockAuthorizedVehiclesTable",
        DynamoTableNameKey.PROVISIONED_VEHICLES_TABLE_NAME.value: "MockProvisionedVehiclesTable",
        "PROVISIONING_TEMPLATE_NAME": "mock_provision_template_name",
        "USER_AGENT_STRING": VPConstants.USER_AGENT_STRING,
        "CLAIM_CERT_PROVISIONING_POLICY_NAME": VPConstants.CLAIM_CERT_PROVISIONING_POLICY_NAME,
        "AWS_REGION": "mock_aws_region",
        "TEST_VIN": "KMHFG4JG1CA181127",
        "TEST_CERTIFICATE_ID": "0123456789012345678901234567890123456789012345678901234567890123",  # Must be exactly 64 characters
    }
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


# Prevents boto from accidentally using default AWS credentials if not mocked
@pytest.fixture(scope="session", autouse=True)
def fixture_aws_credentials() -> None:
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"  # nosec
    os.environ["AWS_SECRET_ACCESS_ID"] = "testing"  # nosec
    os.environ["AWS_SECURITY_TOKEN"] = "testing"  # nosec
    os.environ["AWS_SESSION_TOKEN"] = "testing"  # nosec
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"  # nosec
