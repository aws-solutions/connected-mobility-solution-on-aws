# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import importlib

# mypy: disable-error-code=misc
from typing import Any
from unittest.mock import MagicMock

# Third Party Libraries
import pytest

# AWS Libraries
from botocore.stub import Stubber

# Connected Mobility Solution on AWS
from .....handlers.time_range_handler.function.request_type import RequestType

# pylint: disable=W0212 # Due to runtime import, pylint thinks methods in main are private


@pytest.fixture(name="time_range_handler")
def fixture_time_range_handler() -> Any:
    # Connected Mobility Solution on AWS
    # pylint: disable=C0415
    from .....handlers.time_range_handler.function import main

    return importlib.reload(main)


MOCK_CURRENT_TIMESTREAM_TIME_ISO_STR = "2024-01-02 12:00:00.123000000"
MOCK_SSM_LAST_UNLOAD_TIME_ISO_STR = "2024-01-02 10:00:00.456000"


def ssm_get_unload_time_stubber_builder(
    stubber: Stubber,
    mock_boto3_client: MagicMock,
    unload_end_time_parameter: str,
    last_unload_timestamp_str: str,
) -> None:
    expected_params = {"Name": unload_end_time_parameter, "WithDecryption": True}

    response_data = {"Parameter": {"Value": last_unload_timestamp_str}}

    stubber.add_response("get_parameter", response_data, expected_params)
    mock_boto3_client("ssm", return_value=stubber.client)


def ssm_set_last_unload_end_time_stubber_builder(
    stubber: Stubber,
    mock_boto3_client: MagicMock,
    unload_end_time_parameter: str,
    unload_end_time_str: str,
) -> None:
    expected_params = {
        "Name": unload_end_time_parameter,
        "Value": unload_end_time_str,
        "Type": "String",
        "Overwrite": True,
    }

    response_data = {
        "Version": 1,
    }

    stubber.add_response("put_parameter", response_data, expected_params)
    mock_boto3_client("ssm", return_value=stubber.client)


def timestream_query_time_stubber_builder(
    stubber: Stubber, mock_boto3_client: MagicMock, current_timestamp_str: str
) -> None:
    expected_params = {"QueryString": "SELECT current_timestamp"}
    response_data = {
        "Rows": [{"Data": [{"ScalarValue": current_timestamp_str}]}],
        "QueryId": "query-id",
        "ColumnInfo": [],
    }

    stubber.add_response("query", response_data, expected_params)

    mock_boto3_client("timestream-query", return_value=stubber.client)


def test_get_next_query_start_and_end(
    mock_boto3_client: MagicMock,
    timestream_client_stubber: Stubber,
    ssm_client_stubber: Stubber,
    time_range_handler: Any,
) -> None:
    timestream_query_time_stubber_builder(
        stubber=timestream_client_stubber,
        mock_boto3_client=mock_boto3_client,
        current_timestamp_str=MOCK_CURRENT_TIMESTREAM_TIME_ISO_STR,
    )

    ssm_get_unload_time_stubber_builder(
        stubber=ssm_client_stubber,
        mock_boto3_client=mock_boto3_client,
        unload_end_time_parameter=time_range_handler.ConfigConstants.UNLOAD_END_TIME_PARAMETER_NAME,
        last_unload_timestamp_str=MOCK_SSM_LAST_UNLOAD_TIME_ISO_STR,
    )

    event = {"requestType": RequestType.GET.value}

    result = time_range_handler.handler(event, None)

    current_time = time_range_handler._timestream_iso_string_to_datetime(
        MOCK_CURRENT_TIMESTREAM_TIME_ISO_STR
    )
    next_unload_end_time = time_range_handler._subtract_minutes_from_timestamp(
        timestamp=current_time,
        minutes=time_range_handler.ConfigConstants.TIMESTREAM_QUERY_LAG_BEHIND_MINUTES,
    )
    next_unload_end_time_str = time_range_handler._datetime_to_timestream_iso_string(
        next_unload_end_time
    )

    expected_result = {
        "lastUnloadEndTime": MOCK_SSM_LAST_UNLOAD_TIME_ISO_STR,
        "nextUnloadEndTime": next_unload_end_time_str,
    }

    assert expected_result == result


def test_get_next_query_start_and_end_when_no_last_time(
    mock_boto3_client: MagicMock,
    timestream_client_stubber: Stubber,
    ssm_client_stubber: Stubber,
    time_range_handler: Any,
) -> None:
    timestream_query_time_stubber_builder(
        stubber=timestream_client_stubber,
        mock_boto3_client=mock_boto3_client,
        current_timestamp_str=MOCK_CURRENT_TIMESTREAM_TIME_ISO_STR,
    )

    ssm_get_unload_time_stubber_builder(
        stubber=ssm_client_stubber,
        mock_boto3_client=mock_boto3_client,
        unload_end_time_parameter=time_range_handler.ConfigConstants.UNLOAD_END_TIME_PARAMETER_NAME,
        last_unload_timestamp_str="",
    )

    event = {"requestType": RequestType.GET.value}

    result = time_range_handler.handler(event, None)

    current_time = time_range_handler._timestream_iso_string_to_datetime(
        MOCK_CURRENT_TIMESTREAM_TIME_ISO_STR
    )
    next_unload_end_time = time_range_handler._subtract_minutes_from_timestamp(
        timestamp=current_time,
        minutes=time_range_handler.ConfigConstants.TIMESTREAM_QUERY_LAG_BEHIND_MINUTES,
    )
    next_unload_end_time_str = time_range_handler._datetime_to_timestream_iso_string(
        next_unload_end_time
    )

    last_unload_end_time = time_range_handler._subtract_minutes_from_timestamp(
        timestamp=current_time,
        minutes=time_range_handler.ConfigConstants.DEFAULT_RELATIVE_UNLOAD_START_TIME_INTERVAL_MINUTES,
    )
    last_unload_end_time_str = time_range_handler._datetime_to_timestream_iso_string(
        last_unload_end_time
    )

    expected_result = {
        "lastUnloadEndTime": last_unload_end_time_str,
        "nextUnloadEndTime": next_unload_end_time_str,
    }

    assert expected_result == result


def test_set_last_unload_end_time(
    mock_boto3_client: MagicMock,
    ssm_client_stubber: Stubber,
    time_range_handler: Any,
) -> None:
    ssm_set_last_unload_end_time_stubber_builder(
        stubber=ssm_client_stubber,
        mock_boto3_client=mock_boto3_client,
        unload_end_time_parameter=time_range_handler.ConfigConstants.UNLOAD_END_TIME_PARAMETER_NAME,
        unload_end_time_str=MOCK_CURRENT_TIMESTREAM_TIME_ISO_STR,
    )

    event = {
        "requestType": RequestType.SET.value,
        "timeInfo": {"nextUnloadEndTime": MOCK_CURRENT_TIMESTREAM_TIME_ISO_STR},
    }

    result = time_range_handler.handler(event, None)

    expected_result = {
        "success": True,
    }

    assert expected_result == result
