# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0


# Standard Library
import os

# mypy: disable-error-code=misc
from typing import Any, Dict

# Third Party Libraries
import pytest
import responses
from aws_lambda_powertools.utilities.typing import LambdaContext

# Connected Mobility Solution on AWS
from ....handlers.vehicle_trigger_alarm.lib.custom_exceptions import (
    SendAlertError,
    TokenExchangeError,
)
from ....handlers.vehicle_trigger_alarm.main import get_token_url, handler


@responses.activate
def test_vehicle_trigger_alarm_handler_success(
    vehicle_trigger_alarm_event: Dict[str, Any],
    context: LambdaContext,
) -> None:
    responses.add(
        responses.POST,
        url=get_token_url(),
        json={"access_token": "aa.bb.cc"},
        status=200,
    )
    responses.add(
        responses.POST,
        url=f'{os.environ["ALERTS_PUBLISH_ENDPOINT_URL"]}',
        json={},
        status=200,
    )

    handler(event=vehicle_trigger_alarm_event, context=context)


@responses.activate
def test_vehicle_trigger_alarm_handler_authentication_fail(
    vehicle_trigger_alarm_event: Dict[str, Any],
    context: LambdaContext,
) -> None:
    responses.add(
        responses.POST,
        url=get_token_url(),
        json={},
        status=400,
    )
    responses.add(
        responses.POST,
        url=f'{os.environ["ALERTS_PUBLISH_ENDPOINT_URL"]}',
        json={},
        status=200,
    )

    with pytest.raises(TokenExchangeError):
        handler(event=vehicle_trigger_alarm_event, context=context)


@responses.activate
def test_vehicle_trigger_alarm_handler_send_alert_fail(
    vehicle_trigger_alarm_event: Dict[str, Any],
    context: LambdaContext,
) -> None:
    responses.add(
        responses.POST,
        url=get_token_url(),
        json={"access_token": "aa.bb.cc"},
        status=200,
    )
    responses.add(
        responses.POST,
        url=f'{os.environ["ALERTS_PUBLISH_ENDPOINT_URL"]}',
        json={},
        status=400,
    )

    with pytest.raises(SendAlertError):
        handler(event=vehicle_trigger_alarm_event, context=context)
