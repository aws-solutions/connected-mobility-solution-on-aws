# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any, Dict
from unittest.mock import MagicMock

# AWS Libraries
from aws_lambda_powertools.utilities.typing import LambdaContext

# Connected Mobility Solution on AWS
from ..main import handler
from .fixture_aws_resource_lookup_function import TEST_IDENTITY_PROVIDER_ID


def test_handler(
    aws_resource_lookup_event_identity_provider_id: Dict[str, Any],
    context: LambdaContext,
    mock_boto_identity_provider_id_ssm_parameter: None,
    mocker: MagicMock,
) -> None:
    mocked_requests: MagicMock = mocker.patch(
        "requests.put",
    )

    expected_response = {
        "Status": "SUCCESS",
        "Data": {"parameter_value": TEST_IDENTITY_PROVIDER_ID},
    }

    response = handler(aws_resource_lookup_event_identity_provider_id, context)

    mocked_requests.assert_called_once()
    assert response == expected_response
