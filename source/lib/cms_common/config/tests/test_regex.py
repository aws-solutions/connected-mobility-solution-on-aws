# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import re

# Third Party Libraries
import pytest

# Connected Mobility Solution on AWS
from ..regex import RegexPattern


@pytest.mark.parametrize(
    "pattern, value, valid",
    [
        (RegexPattern.EMAIL, "jie_liu@example.com", True),
        (RegexPattern.EMAIL, "jie.liu@example.com", True),
        (RegexPattern.EMAIL, "abc.123@example.com", True),
        (RegexPattern.EMAIL, "jie_liu+tag@example.com", True),
        (RegexPattern.EMAIL, "jie_liu+first+second@example.com", True),
        (RegexPattern.EMAIL, "jie_liu@example", False),
        (RegexPattern.EMAIL, "_jie_liu@example", False),
        (RegexPattern.EMAIL, "jie_liu@", False),
        (RegexPattern.EMAIL, "jie_liu", False),
        (RegexPattern.EMAIL, "a", False),
        (RegexPattern.DOMAIN_NAME, "example.com", True),
        (RegexPattern.DOMAIN_NAME, "a.example.jp", True),
        (RegexPattern.DOMAIN_NAME, "123.example123.co.in", True),
        (RegexPattern.DOMAIN_NAME, "exam-ple.com", True),
        (RegexPattern.DOMAIN_NAME, "example.c", True),
        (RegexPattern.DOMAIN_NAME, "example.", False),
        (RegexPattern.DOMAIN_NAME, "-example.com", False),
        (RegexPattern.DOMAIN_NAME, "123@example", False),
        (RegexPattern.DOMAIN_NAME, "example", False),
        (RegexPattern.DOMAIN_NAME, "ex$mple.com", False),
        (RegexPattern.GENERIC_NAME, "backstage name", True),
        (RegexPattern.GENERIC_NAME, "123 org", True),
        (RegexPattern.GENERIC_NAME, "name @123", False),
        (RegexPattern.GENERIC_NAME, "backstage.name", False),
        (RegexPattern.GENERIC_NAME, " backstage", False),
        (RegexPattern.GENERIC_NAME, " ", False),
        (RegexPattern.CALLBACK_URLS, "myapp://valid.com", True),
        (RegexPattern.CALLBACK_URLS, "my+app://valid.com", True),
        (RegexPattern.CALLBACK_URLS, "http://localhost", True),
        (RegexPattern.CALLBACK_URLS, "https://hostname:0000/valid", True),
        (RegexPattern.CALLBACK_URLS, "myapp:/invalid.com", False),
        (RegexPattern.CALLBACK_URLS, "myapp://invalid.com#fragment", False),
        (RegexPattern.CALLBACK_URLS, "http://invalid.com", False),
        (RegexPattern.CALLBACK_URLS, "", False),
        (
            RegexPattern.SECRETSMANAGER_SECRET_ARN,
            "arn:aws:secretsmanager:us-east-1:111111111111:secret:/solution/auth/cms/client-config/default-74hfa7",
            True,
        ),
        (
            RegexPattern.SECRETSMANAGER_SECRET_ARN,
            "",
            True,
        ),
        (
            RegexPattern.SECRETSMANAGER_SECRET_ARN,
            "invalid",
            False,
        ),
        (
            RegexPattern.SECRETSMANAGER_SECRET_ARN,
            "arn:aws:secretsmanager:us-east-1:1111111111119:secret:/solution/auth/cms/client-config/default-74hfa7",
            False,
        ),
        (
            RegexPattern.SECRETSMANAGER_SECRET_ARN,
            "arn:aws:secretsmanager:us-west-2:111111111111:secret:/solution/auth/cms/client-config/default-74hfa7",
            True,
        ),
        (
            RegexPattern.SECRETSMANAGER_SECRET_ARN,
            "arn:aws:secretsmanager::111111111111:secret:/solution/auth/cms/client-config/default-74hfa7",
            False,
        ),
        (RegexPattern.BEARER_TOKEN_AUTH_HEADER, "Bearer xxx.yyy.zzz", True),
        (RegexPattern.BEARER_TOKEN_AUTH_HEADER, "Bearer xxx.yyy", False),
        (RegexPattern.BEARER_TOKEN_AUTH_HEADER, "xxx.yyy.zzz", False),
    ],
)
def test_regex_pattern(pattern: str, value: str, valid: bool) -> None:
    match = re.match(pattern, value)
    assert (match is not None) == valid
