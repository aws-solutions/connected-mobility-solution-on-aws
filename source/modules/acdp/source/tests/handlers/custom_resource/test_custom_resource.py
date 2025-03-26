# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any, Callable, Dict
from unittest.mock import MagicMock

# Third Party Libraries
import pytest
from moto import mock_aws

# AWS Libraries
from aws_lambda_powertools.utilities.typing import LambdaContext

# Connected Mobility Solution on AWS
from ....handlers.custom_resource.function.main import (
    create_and_upload_default_users_and_groups,
    create_deployment_uuid,
    handler,
)


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


@mock_aws
def test_create_and_upload_default_users_and_groups_success(
    custom_resource_create_and_upload_default_users_and_groups_event: Dict[str, Any],
    mock_s3_bucket: Callable[[], None],
) -> None:
    mock_s3_bucket()
    create_and_upload_default_users_and_groups(
        custom_resource_create_and_upload_default_users_and_groups_event
    )


def test_create_and_upload_default_users_and_groups_failure(
    custom_resource_create_and_upload_default_users_and_groups_event: Dict[str, Any]
) -> None:
    with pytest.raises(Exception):
        create_and_upload_default_users_and_groups(
            custom_resource_create_and_upload_default_users_and_groups_event
        )
