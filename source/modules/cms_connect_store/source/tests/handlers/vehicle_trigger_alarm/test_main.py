# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0


# Standard Library
from typing import Any, Dict

# Third Party Libraries
import pytest
import responses

# AWS Libraries
from aws_lambda_powertools.utilities.typing import LambdaContext

# Connected Mobility Solution on AWS
from ....handlers.vehicle_trigger_alarm.function.lib.custom_exceptions import (
    ClientAuthenticationError,
    VehicleTriggerAlarmError,
)
from ....handlers.vehicle_trigger_alarm.function.main import handler
from ..fixtures.fixture_vehicle_trigger_alarm import (
    MOCKED_ALERTS_PUBLISH_URL,
    MOCKED_TOKEN_ENDPOINT,
)


@responses.activate
def test_vehicle_trigger_alarm_handler_success(
    mock_vehicle_trigger_alarm_environment_valid: None,
    mock_boto_client_config_valid: None,
    vehicle_trigger_alarm_event: Dict[str, Any],
    context: LambdaContext,
) -> None:
    responses.add(
        responses.POST,
        MOCKED_TOKEN_ENDPOINT,
        json={"access_token": "test_token"},
        status=200,
    )
    responses.add(
        responses.POST, MOCKED_ALERTS_PUBLISH_URL, json={"success": "true"}, status=200
    )

    # verify above requests are made
    handler(vehicle_trigger_alarm_event, context)


@responses.activate
def test_vehicle_trigger_alarm_handler_authentication_fail(
    mock_vehicle_trigger_alarm_environment_valid: None,
    mock_boto_client_config_valid: None,
    vehicle_trigger_alarm_event: Dict[str, Any],
    context: LambdaContext,
) -> None:
    responses.add(
        responses.POST,
        url=MOCKED_TOKEN_ENDPOINT,
        json={},
        status=400,
    )
    responses.add(
        responses.POST,
        url=MOCKED_ALERTS_PUBLISH_URL,
        json={},
        status=200,
    )

    with pytest.raises(ClientAuthenticationError):
        handler(event=vehicle_trigger_alarm_event, context=context)


@responses.activate
def test_vehicle_trigger_alarm_handler_send_alert_fail(
    mock_vehicle_trigger_alarm_environment_valid: None,
    mock_boto_client_config_valid: None,
    vehicle_trigger_alarm_event: Dict[str, Any],
    context: LambdaContext,
) -> None:
    responses.add(
        responses.POST,
        url=MOCKED_TOKEN_ENDPOINT,
        json={"access_token": "aa.bb.cc"},
        status=200,
    )
    responses.add(
        responses.POST,
        url=MOCKED_ALERTS_PUBLISH_URL,
        json={},
        status=400,
    )

    with pytest.raises(VehicleTriggerAlarmError):
        handler(event=vehicle_trigger_alarm_event, context=context)
