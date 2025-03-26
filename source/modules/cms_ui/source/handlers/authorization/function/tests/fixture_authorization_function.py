# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
from typing import Any, Dict

# Third Party Libraries
import pytest

# Connected Mobility Solution on AWS
from .test_main import AuthorizationAPICallBooleans


@pytest.fixture(name="mock_env_for_authorization")
def mock_env_for_authorization() -> None:
    os.environ.update(
        {
            "USER_POOL_REGION": "us-east-1",
            "TOKEN_VALIDATION_LAMBDA_ARN": "arn:aws:lambda:eu-west-1:809313241:function:test",
            "AUTHORIZATION_AUD": "clientId",
        }
    )


@pytest.fixture(name="valid_authorization_event")
def fixture_valid_authorization_event() -> Dict[str, Any]:
    return {"headers": {"Authorization": "valid.test.token"}}


@pytest.fixture(name="invalid_authorization_event")
def fixture_invalid_authorization_event() -> Dict[str, Any]:
    return {"incorrect_field": "throws error"}


@pytest.fixture(name="reset_api_booleans", autouse=True)
def fixture_reset_api_booleans() -> None:
    AuthorizationAPICallBooleans.reset_values()


@pytest.fixture(name="authorization_deny_policy")
def fixture_authorization_deny_policy() -> Dict[str, Any]:
    return {
        "principalId": "*",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "*",
                    "Effect": "Deny",
                    "Resource": "*",
                }
            ],
        },
    }


@pytest.fixture(name="authorization_allow_policy")
def fixture_authorization_allow_policy() -> Dict[str, Any]:
    return {
        "principalId": "*",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "*",
                    "Effect": "Allow",
                    "Resource": "*",
                }
            ],
        },
    }
