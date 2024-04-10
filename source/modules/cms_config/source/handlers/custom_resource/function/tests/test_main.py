# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any, Dict
from unittest.mock import MagicMock

# AWS Libraries
from aws_lambda_powertools.utilities.typing import LambdaContext

# Connected Mobility Solution on AWS
from ..main import create_deployment_uuid, handler


def test_handler(
    custom_resource_create_deployment_uuid_event: Dict[str, Any],
    context: LambdaContext,
    mocker: MagicMock,
) -> None:
    mocked_requests: MagicMock = mocker.patch(
        "requests.put",
    )
    mocked_uuid: MagicMock = mocker.patch("uuid.uuid4")
    mocked_uuid.return_value = "11111111-2222-3333-4444-555555555555"

    expected_response = {
        "Status": "SUCCESS",
        "Data": {"SolutionUUID": mocked_uuid.return_value},
    }

    response = handler(custom_resource_create_deployment_uuid_event, context)

    mocked_requests.assert_called_once()

    assert response == expected_response


def test_create_deployment_uuid(
    custom_resource_create_deployment_uuid_event: Dict[str, Any]
) -> None:
    response = create_deployment_uuid(custom_resource_create_deployment_uuid_event)
    deployment_uuid = response["SolutionUUID"]
    assert isinstance(deployment_uuid, str)
    assert len(deployment_uuid) == 36
