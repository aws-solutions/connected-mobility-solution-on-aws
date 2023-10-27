# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
# mypy: disable-error-code=misc
from typing import Any, Dict
from unittest import mock

# Third Party Libraries
from aws_lambda_powertools.utilities.typing import LambdaContext

# Connected Mobility Solution on AWS
from ....handlers.user_subscriptions import main
from ....handlers.user_subscriptions.lib.dynamo_crud import DynHelpers


def test_get_user_subscriptions(
    user_subscriptions_get_event: Dict[str, Any], mocker: mock.MagicMock
) -> None:
    mock_dyn_query_object = mocker.patch.object(
        DynHelpers,
        "dyn_query",
        return_value=[
            {
                "email": "test-email",
                "vin": "test-vin",
                "alarm_type": "test-alarm-type",
            },
            {
                "email": "test-email",
                "vin": "test-vin1",
                "alarm_type": "test-alarm-type1",
            },
        ],
    )

    expected_response = {
        "email": "test-email",
        "alarms": [
            {
                "vin": "test-vin",
                "alarmType": "test-alarm-type",
            },
            {
                "vin": "test-vin1",
                "alarmType": "test-alarm-type1",
            },
        ],
    }

    response = main.get_user_subscriptions(user_subscriptions_get_event["arguments"])

    mock_dyn_query_object.assert_called_once()
    assert response == expected_response


def test_get_user_subscriptions_with_subscription_arns(
    user_subscriptions_get_event: Dict[str, Any], mocker: mock.MagicMock
) -> None:
    mock_dyn_query_object = mocker.patch.object(
        DynHelpers,
        "dyn_query",
        return_value=[
            {
                "email": "test-email",
                "vin": "test-vin",
                "alarm_type": "test-alarm-type",
                "subscription_arn": "test-subscription-arn",
                "topic_key": "test-vin-alarmtype-sort-key",
            },
            {
                "email": "test-email",
                "vin": "test-vin1",
                "alarm_type": "test-alarm-type1",
                "subscription_arn": "test-subscription-arn1",
                "topic_key": "test-vin-alarmtype-sort-key1",
            },
        ],
    )

    expected_response = {
        "email": "test-email",
        "alarms": [
            {
                "vin": "test-vin",
                "alarm_type": "test-alarm-type",
                "subscription_arn": "test-subscription-arn",
                "topic_key": "test-vin-alarmtype-sort-key",
            },
            {
                "vin": "test-vin1",
                "alarm_type": "test-alarm-type1",
                "subscription_arn": "test-subscription-arn1",
                "topic_key": "test-vin-alarmtype-sort-key1",
            },
        ],
    }

    response = main.get_user_subscriptions_with_subscription_arns(
        user_subscriptions_get_event["arguments"]["email"]
    )

    mock_dyn_query_object.assert_called_once()

    assert response == expected_response


def test_update_user_subscriptions(
    user_subscriptions_update_event: Dict[str, Any], mocker: mock.MagicMock
) -> None:
    mock_dyn_batch_write_object = mocker.patch.object(DynHelpers, "dyn_batch_write")

    mock_boto_client_object = mocker.patch(
        "botocore.client.BaseClient._make_api_call",
        return_value={
            "SubscriptionArn": "test-subscription-arn",
            "TopicArn": "test-topic-arn",
        },
    )

    mock_get_user_subscriptions_with_subscription_arns_object = mocker.patch.object(
        main,
        "get_user_subscriptions_with_subscription_arns",
        return_value={
            "email": "test-email",
            "alarms": [
                {
                    "vin": "test-vin",
                    "alarm_type": "test-alarm-type",
                    "subscription_arn": "test-subscription-arn",
                    "topic_key": "test-vin-alarmtype-sort-key",
                },
                {
                    "vin": "test-vin1",
                    "alarm_type": "test-alarm-type1",
                    "subscription_arn": "test-subscription-arn1",
                    "topic_key": "test-vin-alarmtype-sort-key1",
                },
            ],
        },
    )

    response = main.update_user_subscriptions(
        user_subscriptions_update_event["arguments"]
    )

    mock_dyn_batch_write_object.assert_called_once()
    mock_boto_client_object.assert_called()
    mock_get_user_subscriptions_with_subscription_arns_object.assert_called_once()

    assert response is True


def test_user_subscriptions_handler(
    user_subscriptions_handler_event: Dict[str, Any],
    context: LambdaContext,
    mocker: mock.MagicMock,
) -> None:
    expected_response = [
        {
            "email": "test-email",
            "vin": "test-vin",
            "alarmType": "test-alarm-type",
        },
        {
            "email": "test-email",
            "vin": "test-vin1",
            "alarmType": "test-alarm-type1",
        },
    ]

    mocker.patch.object(main, "get_user_subscriptions", return_value=expected_response)

    response = main.handler(user_subscriptions_handler_event, context)

    assert response == expected_response
