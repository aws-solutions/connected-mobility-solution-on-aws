# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
# Standard Library
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

# AWS Libraries
import boto3
from aws_lambda_powertools import Logger, Tracer
from botocore.config import Config

# Connected Mobility Solution on AWS
from .request_type import RequestType

tracer = Tracer()
logger = Logger()


@dataclass(frozen=True)
class ConfigConstants:

    UNLOAD_END_TIME_PARAMETER_NAME = os.environ["UNLOAD_END_TIME_PARAMETER_NAME"]
    MINUTES_IN_A_DAY_STR = "1440"
    DEFAULT_TIMESTREAM_QUERY_LAG_BEHIND_MINUTES = "1"
    # NOTE: Timestream provides 8 digits of milliseconds, but python only supports 6, so in order to use the TIMESTAMP format for validation, we have to shorten to [:26] chars when used
    TIMESTREAM_TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S.%f"
    DEFAULT_RELATIVE_UNLOAD_START_TIME_INTERVAL_MINUTES = float(
        os.environ.get(
            "DEFAULT_RELATIVE_UNLOAD_START_TIME_INTERVAL_MINUTES", MINUTES_IN_A_DAY_STR
        )
    )
    # Number of minutes to query behind actual time to handle latency for fleetwise to timestream writes.
    TIMESTREAM_QUERY_LAG_BEHIND_MINUTES = float(
        os.environ.get(
            "TIMESTREAM_QUERY_LAG_BEHIND_MINUTES",
            DEFAULT_TIMESTREAM_QUERY_LAG_BEHIND_MINUTES,
        )
    )


@tracer.capture_lambda_handler
def handler(event: Dict[str, Any], _: Any) -> Dict[str, Any]:

    match event["requestType"]:
        case RequestType.GET.value:
            return get_next_query_start_and_end_time()
        case RequestType.SET.value:
            return set_last_unload_end_time(event)
        case _:
            raise ValueError("Invalid Request Type")


def get_next_query_start_and_end_time() -> Dict[str, str]:

    current_timestream_time_str = _get_timestream_current_time()
    current_timestream_time = _timestream_iso_string_to_datetime(
        current_timestream_time_str
    )

    current_time_with_query_shift = _subtract_minutes_from_timestamp(
        timestamp=current_timestream_time,
        minutes=ConfigConstants.TIMESTREAM_QUERY_LAG_BEHIND_MINUTES,
    )
    current_time_with_query_shift_str = _datetime_to_timestream_iso_string(
        current_time_with_query_shift
    )

    last_unload_end_time_str = _get_last_unload_end_time_from_ssm()

    if (
        last_unload_end_time_str is None
        or _timestamp_is_valid_format_for_timestream(last_unload_end_time_str)
        is not True
    ):
        last_unload_end_time = _subtract_minutes_from_timestamp(
            timestamp=current_timestream_time,
            minutes=ConfigConstants.DEFAULT_RELATIVE_UNLOAD_START_TIME_INTERVAL_MINUTES,
        )
        last_unload_end_time_str = _datetime_to_timestream_iso_string(
            last_unload_end_time
        )
    else:
        last_unload_end_time = _subtract_minutes_from_timestamp(
            timestamp=_timestream_iso_string_to_datetime(last_unload_end_time_str),
            minutes=ConfigConstants.DEFAULT_RELATIVE_UNLOAD_START_TIME_INTERVAL_MINUTES,
        )

    logger.info("current_timestream_time: %s", current_timestream_time_str)
    logger.info("current_time_with_query_shift: %s", current_time_with_query_shift_str)
    logger.info("last_unload_end_time: %s", last_unload_end_time_str)

    if last_unload_end_time >= current_time_with_query_shift:
        raise RuntimeError(
            "Current time with query shift is before the last query end time.  Wait until <current time - query shift minutes> is greater than the <last query end time>"
        )

    return {
        "lastUnloadEndTime": last_unload_end_time_str,
        "nextUnloadEndTime": current_time_with_query_shift_str,
    }


def set_last_unload_end_time(event: Dict[str, Any]) -> Dict[str, Any]:

    unload_end_time_str = event["timeInfo"]["nextUnloadEndTime"]

    # Validate that the provided string is a valid timestream timestamp
    _timestream_iso_string_to_datetime(unload_end_time_str)

    ssm = boto3.client(
        "ssm",
        config=Config(
            user_agent_extra=os.environ["USER_AGENT_STRING"],
        ),
    )

    ssm.put_parameter(
        Name=ConfigConstants.UNLOAD_END_TIME_PARAMETER_NAME,
        Value=unload_end_time_str,
        Type="String",
        Overwrite=True,
    )

    return {"success": True}


def _subtract_minutes_from_timestamp(timestamp: datetime, minutes: float) -> datetime:
    return timestamp - timedelta(minutes=minutes)


def _timestream_iso_string_to_datetime(timestamp_str: str) -> datetime:
    return datetime.strptime(
        timestamp_str[:26], ConfigConstants.TIMESTREAM_TIMESTAMP_FORMAT
    )


def _datetime_to_timestream_iso_string(timestamp: datetime) -> str:
    return timestamp.strftime(ConfigConstants.TIMESTREAM_TIMESTAMP_FORMAT)


def _timestamp_is_valid_format_for_timestream(timestamp_str: str | None) -> bool:

    if timestamp_str is not None:
        try:
            _timestream_iso_string_to_datetime(timestamp_str)
            return True
        except (ValueError, TypeError):
            pass

    return False


def _get_timestream_current_time() -> str:
    timestream_client = boto3.client(
        "timestream-query",
        config=Config(
            user_agent_extra=os.environ["USER_AGENT_STRING"],
        ),
    )

    timestream_timestamp_query = "SELECT current_timestamp"

    current_timestamp_response = timestream_client.query(
        QueryString=timestream_timestamp_query
    )
    current_timestamp_str: str = current_timestamp_response["Rows"][0]["Data"][0][
        "ScalarValue"
    ]

    return current_timestamp_str


def _get_last_unload_end_time_from_ssm() -> Optional[str]:

    ssm = boto3.client(
        "ssm",
        config=Config(
            user_agent_extra=os.environ["USER_AGENT_STRING"],
        ),
    )

    try:
        last_query_end_time_response = ssm.get_parameter(
            Name=ConfigConstants.UNLOAD_END_TIME_PARAMETER_NAME, WithDecryption=True
        )

        if (
            "Parameter" in last_query_end_time_response
            and "Value" in last_query_end_time_response["Parameter"]
            and last_query_end_time_response["Parameter"]["Value"] is not None
        ):
            return last_query_end_time_response["Parameter"]["Value"]
    except ssm.exceptions.ParameterNotFound:
        pass

    return None
