# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
# Standard Library
import os
from typing import TYPE_CHECKING, Any, Dict, List, Optional

# AWS Libraries
import boto3
from botocore.config import Config

if TYPE_CHECKING:
    # Third Party Libraries
    from mypy_boto3_timestream_query.type_defs import QueryResponseTypeDef
else:
    QueryResponseTypeDef = object

DEFAULT_BATCH_SIZE = 100  # 100 is Timestream unload partition limit per query


def _query_timestream(
    query: str, next_token: Optional[str] = None
) -> QueryResponseTypeDef:
    timestream_client = boto3.client(
        "timestream-query",
        config=Config(
            user_agent_extra=os.environ["USER_AGENT_STRING"],
        ),
    )

    response: QueryResponseTypeDef
    if next_token:
        response = timestream_client.query(QueryString=query, NextToken=next_token)
    else:
        response = timestream_client.query(QueryString=query)

    return response


def _build_query_sql(
    timestream_db: str,
    timestream_table: str,
    last_unload_end_time: str,
    next_unload_end_time: str,
) -> str:
    return (
        ""  # nosec
        f"""
            SELECT DISTINCT VehicleVIN
            FROM "{timestream_db}"."{timestream_table}"
            WHERE time > TIMESTAMP '{last_unload_end_time}'
            AND time <= TIMESTAMP '{next_unload_end_time}'
        """
    )


def handler(event: Dict[str, Any], _: Any) -> Dict[str, Any]:
    timestream_db = event["timestream"]["databaseName"]
    timestream_table = event["timestream"]["tableName"]
    last_unload_end_time = event["timeInfo"]["lastUnloadEndTime"]
    next_unload_end_time = event["timeInfo"]["nextUnloadEndTime"]
    batch_size = event.get("batchSize", DEFAULT_BATCH_SIZE)
    next_token = None
    vin_batches: List[List[str]] = [[]]
    batch_pos = 0

    query = _build_query_sql(
        timestream_db=timestream_db,
        timestream_table=timestream_table,
        last_unload_end_time=last_unload_end_time,
        next_unload_end_time=next_unload_end_time,
    )

    while True:
        response = _query_timestream(query, next_token)
        next_token = None if "NextToken" not in response else response["NextToken"]

        for row in response["Rows"]:
            for data in row["Data"]:
                if len(vin_batches[batch_pos]) >= batch_size:
                    vin_batches.append([])
                    batch_pos += 1
                vin_batches[batch_pos].append(data["ScalarValue"])

        if next_token is None:
            return {"vin_batches": vin_batches}
