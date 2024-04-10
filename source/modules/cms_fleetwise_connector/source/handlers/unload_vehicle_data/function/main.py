# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

# AWS Libraries
import boto3

if TYPE_CHECKING:
    # Third Party Libraries
    from mypy_boto3_timestream_query.type_defs import QueryResponseTypeDef
else:
    QueryResponseTypeDef = object


class UnloadOutputFormat(Enum):
    CSV = "csv"
    PARQUET = "parquet"


def _build_unload_query_sql(
    timestream_db: str,
    timestream_table: str,
    s3_bucket: str,
    s3_prefix: str,
    s3_kms_key_arn: str,
    last_unload_end_time: str,
    next_unload_end_time: str,
    available_measure_value_types_select_statement: str,
    vin_field_name: str,
    vins: List[str],
    unload_output_format: UnloadOutputFormat,
) -> str:
    # Timestream fields are defined via FleetWise Timestream documentation
    # https://docs.aws.amazon.com/iot-fleetwise/latest/developerguide/process-visualize-data.html#process-vehicle-data

    in_operator_vins = ", ".join(f"'{vin}'" for vin in vins)

    unload_format_properties = _build_unload_format_properties(
        unload_output_format=unload_output_format
    )

    return f"""
        UNLOAD (
            SELECT
                time,
                vehicleName,
                measure_name,
                {available_measure_value_types_select_statement},
                {vin_field_name} as vin
            FROM "{timestream_db}"."{timestream_table}"
            WHERE {vin_field_name} IN ({in_operator_vins})
            AND time > TIMESTAMP '{last_unload_end_time}'
            AND time <= TIMESTAMP '{next_unload_end_time}'
            ORDER BY time ASC
        )
        TO 's3://{s3_bucket}/{s3_prefix}'
        WITH (
            partitioned_by = ARRAY[ 'vin' ],
            encryption = 'SSE_KMS',
            kms_key = '{s3_kms_key_arn}',
            {unload_format_properties}
        )
    """  # nosec


def _build_unload_format_properties(unload_output_format: UnloadOutputFormat) -> str:
    match unload_output_format:
        case UnloadOutputFormat.CSV:
            return """
                format = 'csv',
                compression = 'none',
                include_header = 'true'
            """
        case UnloadOutputFormat.PARQUET:
            return """
                format = 'parquet',
                compression = 'GZIP'
            """
        case _:
            raise AttributeError("Unsupported UnloadOutputFormat specified")


def _build_measure_value_types_query_sql(
    timestream_db: str, timestream_table: str
) -> str:
    return f'DESCRIBE "{timestream_db}"."{timestream_table}"'  # nosec


def _query_timestream(
    query: str, next_token: Optional[str] = None
) -> QueryResponseTypeDef:
    timestream_client = boto3.client("timestream-query")

    response: QueryResponseTypeDef
    if next_token:
        response = timestream_client.query(QueryString=query, NextToken=next_token)
    else:
        response = timestream_client.query(QueryString=query)

    return response


def _get_measure_value_types_select_statement(
    timestream_db: str, timestream_table: str
) -> str:
    query = _build_measure_value_types_query_sql(
        timestream_db=timestream_db, timestream_table=timestream_table
    )

    table_description_response = _query_timestream(query)

    return _parse_measure_value_types_query_response_into_select_statement(
        table_description_response
    )


def _parse_measure_value_types_query_response_into_select_statement(
    timestream_response: QueryResponseTypeDef,
) -> str:
    measure_values: List[str] = []

    for row in timestream_response["Rows"]:
        if row["Data"][2]["ScalarValue"] == "MEASURE_VALUE":
            measure_values.append(row["Data"][0]["ScalarValue"])

    return ", ".join(measure_value for measure_value in measure_values)


def handler(event: Dict[str, Any], _: Any) -> Dict[str, Any]:
    vins = event["vinBatch"]
    timestream_db = event["timestream"]["databaseName"]
    timestream_table = event["timestream"]["tableName"]
    s3_bucket = event["cmsConnectStore"]["telemetryBucketName"]
    s3_prefix = event["cmsConnectStore"]["telemetryPrefixPath"]
    s3_kms_key_arn = event["cmsConnectStore"]["telemetryBucketKmsKeyArn"]
    last_unload_end_time = event["timeInfo"]["lastUnloadEndTime"]
    next_unload_end_time = event["timeInfo"]["nextUnloadEndTime"]
    vehicle_vin_attribute_name = event["fleetwise"]["vehicleVinAttributeName"]
    unload_output_format_str: str = event.get(
        "timestreamUnloadOutputFormat", UnloadOutputFormat.PARQUET.value
    )
    unload_output_format = UnloadOutputFormat[unload_output_format_str.upper()]
    next_token = None

    available_measure_value_types_select_statement = (
        _get_measure_value_types_select_statement(timestream_db, timestream_table)
    )

    query = _build_unload_query_sql(
        timestream_db=timestream_db,
        timestream_table=timestream_table,
        s3_bucket=s3_bucket,
        s3_prefix=s3_prefix,
        s3_kms_key_arn=s3_kms_key_arn,
        last_unload_end_time=last_unload_end_time,
        next_unload_end_time=next_unload_end_time,
        available_measure_value_types_select_statement=available_measure_value_types_select_statement,
        vin_field_name=vehicle_vin_attribute_name,
        vins=vins,
        unload_output_format=unload_output_format,
    )

    while True:
        response = _query_timestream(query, next_token)
        next_token = None if "NextToken" not in response else response["NextToken"]

        if next_token is None:
            return {"timestream_response": response}
