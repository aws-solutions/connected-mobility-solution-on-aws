# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
# mypy: disable-error-code=misc
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock

# Third Party Libraries
import pytest

# AWS Libraries
from botocore.stub import Stubber

# Connected Mobility Solution on AWS
from .....handlers.query_vehicle_vins.function.main import (
    DEFAULT_BATCH_SIZE,
    _build_query_sql,
    handler,
)


@pytest.fixture(name="event")
def fixture_event() -> Dict[str, Any]:
    return {
        "timestream": {
            "databaseName": "your_database_name",
            "tableName": "your_table_name",
        },
        "timeInfo": {
            "lastUnloadEndTime": "2023-01-01T00:00:00Z",
            "nextUnloadEndTime": "2023-01-02T00:00:00Z",
        },
    }


def timestream_query_stubber_builder(
    stubber: Stubber,
    mock_boto3_client: MagicMock,
    event: Dict[str, Any],
    num_vins: int,
    batch_size: int,
) -> List[List[str]]:
    num_batches = num_vins // batch_size

    if num_vins % batch_size != 0:
        num_batches += 1

    vin_batches: List[List[str]] = []
    start = 1

    if num_vins == 0:
        vin_batches.append([])
    else:
        for _ in range(num_batches):
            end = min(start + batch_size, num_vins + 1)
            vin_batch_list = [f"Vehicle_{i}" for i in range(start, end)]
            vin_batches.append(vin_batch_list)
            start = end

    last_next_token: Optional[str] = None
    for i, _ in enumerate(vin_batches):
        next_token: Optional[str] = None
        if i < len(vin_batches) - 1:
            next_token = f"next-token-{i}"

        expected_params = timestream_query_stubber_param_builder(event, last_next_token)
        response_data = timestream_query_stubber_response_builder(
            vin_batches[i], next_token
        )
        last_next_token = next_token

        stubber.add_response("query", response_data, expected_params)

    mock_boto3_client("timestream-query", return_value=stubber.client)

    return vin_batches


def timestream_query_stubber_param_builder(
    event: Dict[str, Any], next_token: Optional[str] = None
) -> Dict[str, Any]:
    query = {
        "QueryString": _build_query_sql(
            timestream_db=event["timestream"]["databaseName"],
            timestream_table=event["timestream"]["tableName"],
            last_unload_end_time=event["timeInfo"]["lastUnloadEndTime"],
            next_unload_end_time=event["timeInfo"]["nextUnloadEndTime"],
        ),
    }

    if next_token is not None:
        query["NextToken"] = next_token

    return query


def timestream_query_stubber_response_builder(
    vins_batch_list: List[Any],
    next_token: Optional[str],
) -> Dict[str, Any]:
    timestream_rows = [
        {"Data": [{"ScalarValue": vin_value}]} for vin_value in vins_batch_list
    ]

    response = {"Rows": timestream_rows, "QueryId": "query-id", "ColumnInfo": []}

    if next_token is not None:
        response["NextToken"] = next_token

    return response


def test_no_vins(
    mock_boto3_client: MagicMock,
    timestream_client_stubber: Stubber,
    event: Dict[str, Any],
) -> None:
    # with Stubber(timestream_client) as stubber:
    num_vins = 0

    expected_result = timestream_query_stubber_builder(
        stubber=timestream_client_stubber,
        mock_boto3_client=mock_boto3_client,
        event=event,
        num_vins=num_vins,
        batch_size=DEFAULT_BATCH_SIZE,
    )

    result = handler(event, None)

    assert result["vin_batches"] == expected_result


def test_get_vins_single_batch(
    mock_boto3_client: MagicMock,
    timestream_client_stubber: Stubber,
    event: Dict[str, Any],
) -> None:
    num_vins = DEFAULT_BATCH_SIZE

    expected_result = timestream_query_stubber_builder(
        stubber=timestream_client_stubber,
        mock_boto3_client=mock_boto3_client,
        event=event,
        num_vins=num_vins,
        batch_size=DEFAULT_BATCH_SIZE,
    )

    result = handler(event, None)

    assert len(result["vin_batches"]) == 1
    assert result["vin_batches"] == expected_result


def test_get_vins_multiple_batches(
    mock_boto3_client: MagicMock,
    timestream_client_stubber: Stubber,
    event: Dict[str, Any],
) -> None:
    num_batches = 5
    num_vins = num_batches * DEFAULT_BATCH_SIZE

    expected_result = timestream_query_stubber_builder(
        stubber=timestream_client_stubber,
        mock_boto3_client=mock_boto3_client,
        event=event,
        num_vins=num_vins,
        batch_size=DEFAULT_BATCH_SIZE,
    )

    result = handler(event, None)

    assert len(result["vin_batches"]) == num_batches
    assert result["vin_batches"] == expected_result


def test_get_vins_override_batch_size(
    mock_boto3_client: MagicMock,
    timestream_client_stubber: Stubber,
    event: Dict[str, Any],
) -> None:
    override_batch_size = 10
    num_vins = 6288
    event["batchSize"] = override_batch_size

    expected_result = timestream_query_stubber_builder(
        stubber=timestream_client_stubber,
        mock_boto3_client=mock_boto3_client,
        event=event,
        num_vins=num_vins,
        batch_size=override_batch_size,
    )

    result = handler(event, None)

    assert len(result["vin_batches"]) == 629
    assert result["vin_batches"] == expected_result
