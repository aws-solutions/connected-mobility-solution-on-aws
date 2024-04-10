# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
from typing import Any, Dict

# Third Party Libraries
import pytest


@pytest.fixture(name="mock_env_for_authorization")
def mock_env_for_authorization() -> None:
    os.environ.update(
        {
            "USER_POOL_REGION": "us-east-1",
            "TOKEN_VALIDATION_LAMBDA_ARN": "arn:aws:lambda:eu-west-1:809313241:function:test",
        }
    )


@pytest.fixture(name="valid_authorization_event")
def fixture_valid_authorization_event() -> Dict[str, Any]:
    return {"authorizationToken": "Bearer valid.test.token"}


@pytest.fixture(name="invalid_authorization_event")
def fixture_invalid_authorization_event() -> Dict[str, Any]:
    return {"incorrect_field": "throws error"}
