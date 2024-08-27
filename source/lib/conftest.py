# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
from typing import Dict, Generator
from unittest.mock import patch

# Third Party Libraries
import pytest

# isort: off
# pylint: disable=unused-import

# Connected Mobility Solution on AWS
from .cms_common.auth.tests.fixture_auth import (
    fixture_mock_user_client_config_valid,
    fixture_service_client_config_secret_string_valid,
    fixture_idp_config_secret_string_valid,
    fixture_mock_service_client_config_valid,
    fixture_user_client_config_secret_string_valid,
    fixture_mock_idp_config_invalid_data_format,
    fixture_mock_idp_config_invalid_json,
    fixture_mock_idp_config_valid,
)
from .cms_common.boto3_wrappers.tests.fixture_dynamo_crud import (
    fixture_dynamodb_table,
    fixture_mock_dynamo_env_vars,
    fixture_mocked_module_env_vars_values,
)
from .cms_common.config.tests.fixture_config import fixture_solution_config
from .cms_common.constructs.tests.fixture_constructs import (
    fixture_app_unique_id_cfn_parameter,
    fixture_app_unique_id_stack,
    fixture_cdk_lambda_vpc_config_construct_stack_template,
    fixture_custom_resource_lambda_stack,
    fixture_identity_provider_config_stack,
    fixture_empty_lambda_dependencies_stack,
    fixture_populated_lambda_dependencies_stack,
    fixture_snapshot_json_with_matcher,
    fixture_vpc_construct_stack,
    fixture_vpc_construct_stack_template,
    fixture_vpc_construct_subnet_selections,
)

# pylint: enable=unused-import
# isort: on

# TOP LEVEL SHARED FIXTURES
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


@pytest.fixture(scope="session", autouse=True)
def fixture_mock_env_vars(
    aws_credentials_env_vars: Dict[str, str]
) -> Generator[None, None, None]:
    env_vars = {
        **aws_credentials_env_vars,
    }
    with patch.dict(os.environ, env_vars):
        yield
