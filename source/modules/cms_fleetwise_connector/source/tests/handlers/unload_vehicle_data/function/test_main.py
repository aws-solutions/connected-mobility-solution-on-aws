# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
# mypy: disable-error-code=misc
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock

# Third Party Libraries
import pytest
from mypy_boto3_timestream_query.type_defs import QueryResponseTypeDef

# AWS Libraries
from botocore.stub import Stubber

# Connected Mobility Solution on AWS
from .....handlers.unload_vehicle_data.function.main import (
    UnloadOutputFormat,
    _build_measure_value_types_query_sql,
    _build_unload_query_sql,
    _parse_measure_value_types_query_response_into_select_statement,
    handler,
)


@pytest.fixture(name="event")
def fixture_event() -> Dict[str, Any]:
    return {
        "vinBatch": ["Vehicle_1", "Vehicle_2"],
        "timestream": {
            "databaseName": "your_database_name",
            "tableName": "your_table_name",
        },
        "cmsConnectStore": {
            "telemetryBucketName": "bucket-name",
            "telemetryPrefixPath": "bucket-prefix",
        },
        "timeInfo": {
            "lastUnloadEndTime": "2023-01-01T00:00:00Z",
            "nextUnloadEndTime": "2023-01-02T00:00:00Z",
        },
        "fleetwise": {"vehicleVinAttributeName": "VehicleVIN"},
    }


def timestream_available_measure_types_query_stubber_builder(
    stubber: Stubber,
    mock_boto3_client: MagicMock,
    event: Dict[str, Any],
    measure_value_types: List[str],
) -> Dict[str, Any]:
    expected_params = {
        "QueryString": _build_measure_value_types_query_sql(
            timestream_db=event["timestream"]["databaseName"],
            timestream_table=event["timestream"]["tableName"],
        ),
    }
    response_data = generate_available_timestream_measures_response(measure_value_types)

    stubber.add_response("query", response_data, expected_params)

    mock_boto3_client("timestream-query", return_value=stubber.client)

    return response_data


def timestream_unload_query_stubber_builder(
    stubber: Stubber,
    mock_boto3_client: MagicMock,
    event: Dict[str, Any],
    available_measure_value_types_select_statement: str,
    num_queries_required_to_complete_unload: int = 1,
    unload_output_format: UnloadOutputFormat = UnloadOutputFormat.PARQUET,
) -> Dict[str, Any]:
    last_next_token: Optional[str] = None

    total_num_bytes = 1000000000
    total_rows = 1000000

    for query_pos in range(1, num_queries_required_to_complete_unload + 1):
        next_token: Optional[str] = None
        if query_pos < num_queries_required_to_complete_unload:
            next_token = f"next-token-{query_pos}"

            response_data = generate_unload_incremental_response(
                bytes_metered_scanned=int(
                    total_num_bytes
                    * (query_pos / num_queries_required_to_complete_unload)
                ),
                progress_percentage=query_pos / num_queries_required_to_complete_unload,
                next_token=next_token,
            )
        else:
            response_data = generate_unload_complete_response(
                s3_bucket=event["cmsConnectStore"]["telemetryBucketName"],
                s3_prefix=event["cmsConnectStore"]["telemetryPrefixPath"],
                total_rows_unloaded=total_rows,
            )

        expected_params = timestream_unload_query_stubber_param_builder(
            event=event,
            available_measure_value_types_select_statement=available_measure_value_types_select_statement,
            unload_output_format=unload_output_format,
            next_token=last_next_token,
        )

        last_next_token = next_token

        stubber.add_response("query", response_data, expected_params)

    mock_boto3_client("timestream-query", return_value=stubber.client)

    return response_data


def timestream_unload_query_stubber_param_builder(
    event: Dict[str, Any],
    available_measure_value_types_select_statement: str,
    unload_output_format: UnloadOutputFormat,
    next_token: Optional[str] = None,
) -> Dict[str, Any]:
    query = {
        "QueryString": _build_unload_query_sql(
            timestream_db=event["timestream"]["databaseName"],
            timestream_table=event["timestream"]["tableName"],
            s3_bucket=event["cmsConnectStore"]["telemetryBucketName"],
            s3_prefix=event["cmsConnectStore"]["telemetryPrefixPath"],
            last_unload_end_time=event["timeInfo"]["lastUnloadEndTime"],
            next_unload_end_time=event["timeInfo"]["nextUnloadEndTime"],
            vin_field_name=event["fleetwise"]["vehicleVinAttributeName"],
            available_measure_value_types_select_statement=available_measure_value_types_select_statement,
            vins=event["vinBatch"],
            unload_output_format=unload_output_format,
        )
    }

    if next_token is not None:
        query["NextToken"] = next_token

    return query


def generate_available_timestream_measures_response(
    measure_value_types: List[str],
) -> Dict[str, Any]:
    rows = [
        {
            "Data": [
                {"ScalarValue": "eventId"},
                {"ScalarValue": "varchar"},
                {"ScalarValue": "DIMENSION"},
            ]
        },
        {
            "Data": [
                {"ScalarValue": "vehicleName"},
                {"ScalarValue": "varchar"},
                {"ScalarValue": "DIMENSION"},
            ]
        },
        {
            "Data": [
                {"ScalarValue": "VehicleVIN"},
                {"ScalarValue": "varchar"},
                {"ScalarValue": "DIMENSION"},
            ]
        },
        {
            "Data": [
                {"ScalarValue": "campaignName"},
                {"ScalarValue": "varchar"},
                {"ScalarValue": "DIMENSION"},
            ]
        },
        {
            "Data": [
                {"ScalarValue": "measure_name"},
                {"ScalarValue": "varchar"},
                {"ScalarValue": "MEASURE_NAME"},
            ]
        },
        {
            "Data": [
                {"ScalarValue": "time"},
                {"ScalarValue": "timestamp"},
                {"ScalarValue": "TIMESTAMP"},
            ]
        },
    ]

    for measure_value_type in measure_value_types:
        rows.append(
            {
                "Data": [
                    {"ScalarValue": f"measure_value::{measure_value_type}"},
                    {"ScalarValue": measure_value_type},
                    {"ScalarValue": "MEASURE_VALUE"},
                ]
            }
        )

    return {"Rows": rows, "QueryId": "query-id", "ColumnInfo": []}


def generate_unload_complete_response(
    s3_bucket: str, s3_prefix: str, total_rows_unloaded: int
) -> Dict[str, Any]:
    return {
        "ColumnInfo": [],
        "QueryId": "query-id",
        "Rows": [
            {
                "Data": [
                    {"ScalarValue": f"{total_rows_unloaded}"},
                    {
                        "ScalarValue": f"s3://{s3_bucket}/{s3_prefix}/unload_metadata.json"
                    },
                    {
                        "ScalarValue": f"s3://{s3_bucket}/{s3_prefix}/unload_manifest.json"
                    },
                ]
            }
        ],
    }


def generate_unload_incremental_response(
    bytes_metered_scanned: int, progress_percentage: float, next_token: str
) -> Dict[str, Any]:
    return {
        "ColumnInfo": [],
        "NextToken": next_token,
        "QueryId": "query-id",
        "QueryStatus": {
            "CumulativeBytesMetered": bytes_metered_scanned,
            "CumulativeBytesScanned": bytes_metered_scanned,
            "ProgressPercentage": progress_percentage,
        },
        "Rows": [],
    }


def test_unload_one_measure_type_to_csv(
    mock_boto3_client: MagicMock,
    timestream_client_stubber: Stubber,
    event: Dict[str, Any],
) -> None:
    measure_value_types = ["double"]

    event["timestreamUnloadOutputFormat"] = "CSV"
    unload_output_format = UnloadOutputFormat[event["timestreamUnloadOutputFormat"]]

    expected_result_measure_values = (
        timestream_available_measure_types_query_stubber_builder(
            stubber=timestream_client_stubber,
            mock_boto3_client=mock_boto3_client,
            event=event,
            measure_value_types=measure_value_types,
        )
    )

    available_measure_value_types_select_statement = (
        _parse_measure_value_types_query_response_into_select_statement(
            QueryResponseTypeDef(expected_result_measure_values)
        )
    )

    expected_result = timestream_unload_query_stubber_builder(
        stubber=timestream_client_stubber,
        mock_boto3_client=mock_boto3_client,
        event=event,
        available_measure_value_types_select_statement=available_measure_value_types_select_statement,
        num_queries_required_to_complete_unload=1,
        unload_output_format=unload_output_format,
    )

    result = handler(event, None)

    assert result["timestream_response"] == expected_result


def test_unload_one_measure_type_to_parquet(
    mock_boto3_client: MagicMock,
    timestream_client_stubber: Stubber,
    event: Dict[str, Any],
) -> None:
    measure_value_types = ["double"]

    event["timestreamUnloadOutputFormat"] = "PARQUET"
    unload_output_format = UnloadOutputFormat[event["timestreamUnloadOutputFormat"]]

    expected_result_measure_values = (
        timestream_available_measure_types_query_stubber_builder(
            stubber=timestream_client_stubber,
            mock_boto3_client=mock_boto3_client,
            event=event,
            measure_value_types=measure_value_types,
        )
    )

    available_measure_value_types_select_statement = (
        _parse_measure_value_types_query_response_into_select_statement(
            QueryResponseTypeDef(expected_result_measure_values)
        )
    )

    expected_result = timestream_unload_query_stubber_builder(
        stubber=timestream_client_stubber,
        mock_boto3_client=mock_boto3_client,
        event=event,
        available_measure_value_types_select_statement=available_measure_value_types_select_statement,
        num_queries_required_to_complete_unload=1,
        unload_output_format=unload_output_format,
    )

    result = handler(event, None)

    assert result["timestream_response"] == expected_result


def test_unload_next_required(
    mock_boto3_client: MagicMock,
    timestream_client_stubber: Stubber,
    event: Dict[str, Any],
) -> None:
    measure_value_types = ["double"]
    number_of_queries_to_complete_unload = 7

    expected_result_measure_values = (
        timestream_available_measure_types_query_stubber_builder(
            stubber=timestream_client_stubber,
            mock_boto3_client=mock_boto3_client,
            event=event,
            measure_value_types=measure_value_types,
        )
    )

    available_measure_value_types_select_statement = (
        _parse_measure_value_types_query_response_into_select_statement(
            QueryResponseTypeDef(expected_result_measure_values)
        )
    )

    expected_result = timestream_unload_query_stubber_builder(
        stubber=timestream_client_stubber,
        mock_boto3_client=mock_boto3_client,
        event=event,
        available_measure_value_types_select_statement=available_measure_value_types_select_statement,
        num_queries_required_to_complete_unload=number_of_queries_to_complete_unload,
    )

    result = handler(event, None)

    assert result["timestream_response"] == expected_result
