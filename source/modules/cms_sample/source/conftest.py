# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# pylint: disable=unused-import

# Standard Library
import os
from typing import Dict, Generator
from unittest.mock import patch

# Third Party Libraries
import pytest

# Connected Mobility Solution on AWS
from .infrastructure.tests.fixture_infrastructure import (
    fixture_snapshot_json_with_matcher,
)

# pylint: enable=unused-import


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
