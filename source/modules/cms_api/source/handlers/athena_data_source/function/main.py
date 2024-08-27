# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
from collections import defaultdict
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Dict, List, Union

# Third Party Libraries
from backoff import fibo, on_predicate

# AWS Libraries
import boto3
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.config import Config
from botocore.exceptions import ClientError

# Connected Mobility Solution on AWS
from .lib.athena_exceptions import AthenaQueryError
from .lib.operational_metrics import write_metric
from .lib.query_config import QUERY_TYPE_HANDLER

if TYPE_CHECKING:
    # Third Party Libraries
    from mypy_boto3_athena import AthenaClient
else:
    AthenaClient = object

tracer = Tracer()
logger = Logger()


@lru_cache(maxsize=128)
def get_athena_client() -> AthenaClient:
    return boto3.client(
        "athena", config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"])
    )


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(  # pylint: disable=inconsistent-return-statements
    event: Dict[str, Any], context: LambdaContext
) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    try:
        query_type = event["info"]["fieldName"]
        selection_set_list = event["selectionSetList"]
        arguments = event["arguments"]

        if os.environ["REPORT_METRICS_ENABLED"] == "Yes":
            try:
                write_metric(
                    metric_data={
                        "Type": "CMSApiAppSyncRequest",
                        "Request": event["info"]["fieldName"],
                        "RequestType": event["info"]["parentTypeName"],
                    },
                )
            # Catch all exceptions here so that publishing metrics will never break API functionality
            except Exception:  # pylint: disable=broad-exception-caught
                logger.error("Failed to write operational metrics", exc_info=True)

        # Builds query based on query type
        query = QUERY_TYPE_HANDLER[query_type]
        query_string = query.query_string_builder(
            selection_set_list,
            os.environ["GLUE_TABLE_NAME"],
            arguments,
        )

        # Executes query and waits for successful status
        logger.info(f"Executing Query: {query_string}")
        results = execute_query(
            query_string=query_string,
            query_execution_context={"Database": os.environ["GLUE_DATABASE_NAME"]},
            workgroup=os.environ["ATHENA_WORKGROUP"],
            max_time_in_seconds=query.max_time_in_seconds,
        )

        # Processes results into json format consumable by AppSync
        results_json = results_to_json(results)
        return results_json if query.multiple_results else results_json[0]

    except AthenaQueryError as err:
        logger.error(f"Error while running Athena query: {err}")
        raise err

    except KeyError as err:
        logger.error(f"Key Error: {err}")
        raise err

    except ClientError as err:
        logger.error(f"Athena Client Error: {err}")
        raise err


def poll_query_status(
    query_execution_id: str, max_time_in_seconds: int
) -> Dict[str, Any]:
    @on_predicate(
        fibo,
        lambda status: status["State"] not in ("SUCCEEDED", "FAILED", "CANCELLED"),
        max_time=max_time_in_seconds,
    )
    def _get_query_status(query_execution_id: str) -> Dict[str, Any]:
        response = get_athena_client().get_query_execution(
            QueryExecutionId=query_execution_id
        )
        return response["QueryExecution"]["Status"]  # type: ignore[return-value]

    return _get_query_status(query_execution_id)


def execute_query(
    query_string: str,
    query_execution_context: Dict[str, Any],
    workgroup: str,
    max_time_in_seconds: int,
) -> Dict[str, Any]:
    query_execution_id = get_athena_client().start_query_execution(
        QueryString=query_string,
        QueryExecutionContext=query_execution_context,  # type: ignore[arg-type]
        WorkGroup=workgroup,
    )["QueryExecutionId"]
    query_status = poll_query_status(query_execution_id, max_time_in_seconds)
    if query_status["State"] != "SUCCEEDED":
        logger.error(query_status["StateChangeReason"])
        raise AthenaQueryError(
            f"Query execution failed with status {query_status['State']}"
        )
    results = get_athena_client().get_query_results(
        QueryExecutionId=query_execution_id, MaxResults=int(os.environ["RECORD_LIMIT"])
    )
    return results  # type: ignore[return-value]


def results_to_json(unprocessed_results: Dict[str, Any]) -> List[Dict[str, Any]]:
    # Athena returns results in a csv format. These must be parsed to json.

    # Column list with column names that are the json path of that field. Example: vehicleidentification.vin
    column_list = unprocessed_results["ResultSet"]["ResultSetMetadata"]["ColumnInfo"]
    # Data rows. Skips the first row as it contains column names.
    rows = unprocessed_results["ResultSet"]["Rows"][1:]

    # Nested defaultdict whose children are defaultdicts.
    def nested() -> Dict[str, Any]:
        return defaultdict(nested)

    result = []
    # Iterate over each row represents a flattened json.
    for row in rows:
        result_json = nested()
        # Iterate over each column and to get the json path for that column value.
        for i, column in enumerate(column_list):
            current = result_json
            json_path = column["Name"].split(".")
            # Iterate over the json path to build the json object.
            for key in json_path:
                current = current[key]
            current["value"] = row["Data"][i]["VarCharValue"]
        result.append(result_json)

    return result
