# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0


# Standard Library
# mypy: disable-error-code=misc
import json
from typing import Any, Dict
from unittest.mock import MagicMock

# Third Party Libraries
import boto3
from aws_lambda_powertools.utilities.typing import LambdaContext

# Connected Mobility Solution on AWS
from ....handlers.custom_resource.lib.custom_resource_type_enum import (
    CustomResourceType,
)
from ....handlers.custom_resource.main import (
    handler,
    manage_user_pool_domain,
    send_cloud_formation_response,
)


def test_handler(
    custom_resource_manage_user_pool_domain_event: Dict[str, Any],
    context: LambdaContext,
    mocker: MagicMock,
) -> None:
    mocked_requests: MagicMock = mocker.patch("requests.put")
    response = handler(
        event=custom_resource_manage_user_pool_domain_event, context=context
    )

    mocked_requests.assert_called_once()
    assert response["Status"] == CustomResourceType.StatusType.SUCCESS.value


def test_handler_invalid_event(
    custom_resource_event: Dict[str, Any],
    context: LambdaContext,
    mocker: MagicMock,
) -> None:
    mocked_requests: MagicMock = mocker.patch("requests.put")
    response = handler(custom_resource_event, context)

    mocked_requests.assert_called_once()
    assert response["Status"] == CustomResourceType.StatusType.FAILED.value


def test_send_cloud_formation_response(
    custom_resource_event: Dict[str, Any], mocker: MagicMock
) -> None:
    mocked_requests: MagicMock = mocker.patch("requests.put")

    input_response = {
        "Status": "SUCCESS",
        "Data": None,
    }
    reason = "test-reason"

    expected_response = json.dumps(
        {
            "Status": input_response["Status"],
            "Reason": reason,
            "PhysicalResourceId": custom_resource_event["LogicalResourceId"],
            "StackId": custom_resource_event["StackId"],
            "RequestId": custom_resource_event["RequestId"],
            "LogicalResourceId": custom_resource_event["LogicalResourceId"],
            "Data": input_response["Data"],
        }
    )
    headers = {"Content-Type": "application/json"}

    send_cloud_formation_response(custom_resource_event, input_response, reason)

    mocked_requests.assert_called_with(
        custom_resource_event["ResponseURL"],
        data=expected_response,
        headers=headers,
        timeout=60,
    )


def test_manage_user_pool_domain_on_create(
    custom_resource_manage_user_pool_domain_event: Dict[str, Any]
) -> None:
    cognito_client = boto3.client("cognito-idp")

    user_pool_id = custom_resource_manage_user_pool_domain_event["ResourceProperties"][
        "UserPoolId"
    ]
    user_pool = cognito_client.describe_user_pool(UserPoolId=user_pool_id)
    assert user_pool["UserPool"].get("Domain", None) is None

    manage_user_pool_domain(event=custom_resource_manage_user_pool_domain_event)

    user_pool = cognito_client.describe_user_pool(UserPoolId=user_pool_id)
    assert isinstance(user_pool["UserPool"].get("Domain", None), str)


def test_manage_user_pool_domain_on_delete(
    custom_resource_manage_user_pool_domain_event: Dict[str, Any]
) -> None:
    cognito_client = boto3.client("cognito-idp")

    # Create user pool domain
    user_pool_id = custom_resource_manage_user_pool_domain_event["ResourceProperties"][
        "UserPoolId"
    ]
    user_pool = cognito_client.describe_user_pool(UserPoolId=user_pool_id)
    assert user_pool["UserPool"].get("Domain", None) is None

    manage_user_pool_domain(event=custom_resource_manage_user_pool_domain_event)

    user_pool = cognito_client.describe_user_pool(UserPoolId=user_pool_id)
    assert isinstance(user_pool["UserPool"].get("Domain", None), str)

    # Delete user pool domain
    custom_resource_manage_user_pool_domain_event[
        "RequestType"
    ] = CustomResourceType.RequestType.DELETE.value
    manage_user_pool_domain(event=custom_resource_manage_user_pool_domain_event)

    user_pool = cognito_client.describe_user_pool(UserPoolId=user_pool_id)
    assert user_pool["UserPool"].get("Domain", None) is None
