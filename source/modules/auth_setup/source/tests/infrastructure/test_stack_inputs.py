# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import re
from typing import Any, Dict, List

# Third Party Libraries
import pytest


@pytest.mark.parametrize(
    "cfn_parameter_names, cfn_parameter_value, is_valid",
    [
        (["CallbackUrls"], "myapp://valid.com", True),
        (["CallbackUrls"], "my+app://valid.com", True),
        (["CallbackUrls"], "http://localhost", True),
        (["CallbackUrls"], "myapp://invalid.com:edu", False),
        (["CallbackUrls"], "myapp://invalid.com.", False),
        (["CallbackUrls"], "myapp:/invalid.com", False),
        (["CallbackUrls"], "myapp://invalid.com#fragment", False),
        (
            [
                "IdPConfigSecretArn",
                "ServiceClientConfigSecretArn",
                "AuthorizationCodeExchangeConfigSecretArn",
            ],
            "arn:aws:secretsmanager:us-east-1:111111111111:secret:/solution/auth/cms/client-config/default-74hfa7",
            True,
        ),
        (
            [
                "IdPConfigSecretArn",
                "ServiceClientConfigSecretArn",
                "AuthorizationCodeExchangeConfigSecretArn",
            ],
            "",
            True,
        ),
        (
            [
                "IdPConfigSecretArn",
                "ServiceClientConfigSecretArn",
                "AuthorizationCodeExchangeConfigSecretArn",
            ],
            "invalid",
            False,
        ),
        (
            [
                "IdPConfigSecretArn",
                "ServiceClientConfigSecretArn",
                "AuthorizationCodeExchangeConfigSecretArn",
            ],
            "arn:aws:secretsmanager:us-east-1:1111111111119:secret:/solution/auth/cms/client-config/default-74hfa7",
            False,
        ),
        (
            [
                "IdPConfigSecretArn",
                "ServiceClientConfigSecretArn",
                "AuthorizationCodeExchangeConfigSecretArn",
            ],
            "arn:aws:secretsmanager:us-west-2:111111111111:secret:/solution/auth/cms/client-config/default-74hfa7",
            True,
        ),
        (
            [
                "IdPConfigSecretArn",
                "ServiceClientConfigSecretArn",
                "AuthorizationCodeExchangeConfigSecretArn",
            ],
            "arn:aws:secretsmanager::111111111111:secret:/solution/auth/cms/client-config/default-74hfa7",
            False,
        ),
    ],
)
def test_cfn_parameter_validators(
    auth_setup_stack_parameters: Dict[str, Any],
    cfn_parameter_names: List[str],
    cfn_parameter_value: str,
    is_valid: bool,
) -> None:
    for cfn_parameter_name in cfn_parameter_names:
        pattern = auth_setup_stack_parameters[cfn_parameter_name]["AllowedPattern"]
        match = re.match(pattern, cfn_parameter_value)
        assert (match is not None) == is_valid
