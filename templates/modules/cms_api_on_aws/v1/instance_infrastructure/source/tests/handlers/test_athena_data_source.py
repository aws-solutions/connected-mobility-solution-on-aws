# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
# mypy: disable-error-code=misc

# Standard Library
import os
from typing import Any, Dict
from unittest.mock import MagicMock

# Third Party Libraries
import boto3
from aws_lambda_powertools.utilities.typing import LambdaContext
from moto import mock_aws  # type: ignore[import-untyped]

# Connected Mobility Solution on AWS
from ...handlers.athena_data_source.lib.query_config import (
    build_get_vehicle_query,
    build_list_vehicles_query,
)
from ...handlers.athena_data_source.main import execute_query, handler, results_to_json


def test_handler(
    context: LambdaContext,
    athena_data_source_lambda_event: Dict[str, Any],
    mocker: MagicMock,
) -> None:
    mocked_requests: MagicMock = mocker.patch("requests.post")
    response = handler(athena_data_source_lambda_event, context)
    mocked_requests.assert_called_once()
    assert isinstance(response, list)


@mock_aws
def test_execute_query() -> None:
    athena_client = boto3.client("athena")

    test_query_string = 'select * from "test-table"'
    query_execution_context = {"Database": "test-database-name"}
    athena_client.create_work_group(Name=os.environ["ATHENA_WORKGROUP"])

    results = execute_query(
        test_query_string, query_execution_context, os.environ["ATHENA_WORKGROUP"], 10
    )
    assert isinstance(results["ResultSet"], dict)


def test_build_get_vehicle_query(
    athena_data_source_lambda_event: Dict[str, Any]
) -> None:
    selection_set = athena_data_source_lambda_event["selectionSetList"]
    glue_table = "test-glue-table"
    arguments = {"vin": "ABCDEFGHIJ12345678"}

    expected_query_string = (
        'SELECT "json"."path" as "json.path", "another"."json"."path" as "another.json.path" '
        'FROM "test-glue-table" '
        "WHERE vehicleidentification.vin = 'ABCDEFGHIJ12345678' "
        "LIMIT 1"
    )
    query_string = build_get_vehicle_query(selection_set, glue_table, arguments)
    assert query_string == expected_query_string


def test_build_list_vehicle_query(
    athena_data_source_lambda_event: Dict[str, Any]
) -> None:
    selection_set = athena_data_source_lambda_event["selectionSetList"]
    glue_table = "test-glue-table"
    arguments = {"page": 0}

    expected_query_string = (
        'SELECT "json"."path" as "json.path", "another"."json"."path" as "another.json.path" '
        'FROM "test-glue-table" '
        "ORDER BY vehicleidentification.vin "
        "OFFSET 0 LIMIT 100"
    )
    query_string = build_list_vehicles_query(selection_set, glue_table, arguments)
    assert query_string == expected_query_string


def test_results_to_json(unproccessed_athena_query_results: Dict[str, Any]) -> None:
    expected_json_results = [
        {
            "field": {"value": "value-1"},
            "nested": {"field": {"value": "nested-value-1"}},
        },
        {
            "field": {"value": "value-2"},
            "nested": {"field": {"value": "nested-value-2"}},
        },
    ]
    json_result = results_to_json(unproccessed_athena_query_results)
    assert json_result == expected_json_results
