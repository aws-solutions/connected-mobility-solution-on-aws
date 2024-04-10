# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
import pytest

# Connected Mobility Solution on AWS
from ..config import ConfigResourceNames

TEST_APP_UNIQUE_ID = "test-app"

config_resource_names = ConfigResourceNames.from_app_unique_id(TEST_APP_UNIQUE_ID)


@pytest.mark.parametrize(
    "attribute, expected_attribute_value",
    [
        ("config_prefix", f"/solution/{TEST_APP_UNIQUE_ID}/config"),
        (
            "identity_provider_id_ssm_parameter",
            f"/solution/{TEST_APP_UNIQUE_ID}/config/auth/identity-provider-id",
        ),
        (
            "aws_resource_lookup_lambda_arn_ssm_parameter",
            f"/solution/{TEST_APP_UNIQUE_ID}/config/aws-resource-lookup-lambda/arn",
        ),
    ],
)
def test_config(attribute: str, expected_attribute_value: str) -> None:
    assert getattr(config_resource_names, attribute) == expected_attribute_value
