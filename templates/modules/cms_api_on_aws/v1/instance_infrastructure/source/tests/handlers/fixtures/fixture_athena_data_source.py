# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
from typing import Any, Dict, Generator

# Third Party Libraries
import boto3
import pytest
from moto.athena import mock_athena  # type: ignore[import-untyped]


@pytest.fixture(name="athena_data_source_lambda_event")
def fixture_athena_data_source_lambda_event() -> Generator[Dict[str, Any], None, None]:
    with mock_athena():
        athena_client = boto3.client("athena")

        athena_client.create_work_group(Name=os.environ["ATHENA_WORKGROUP"])

        yield {
            "info": {
                "fieldName": "listVehicles",
                "parentTypeName": "Query",
            },
            "selectionSetList": [
                "json",
                "json/path",
                "json/path/value",
                "another",
                "another/json/path",
                "another/json/path/value",
            ],
            "arguments": {"page": "0"},
        }


@pytest.fixture(name="unproccessed_athena_query_results")
def fixture_unproccessed_athena_query_results() -> Dict[str, Any]:
    return {
        "ResultSet": {
            "Rows": [
                {
                    "Data": [
                        {"VarCharValue": "field"},
                        {"VarCharValue": "nested.field"},
                    ],
                },
                {
                    "Data": [
                        {"VarCharValue": "value-1"},
                        {"VarCharValue": "nested-value-1"},
                    ],
                },
                {
                    "Data": [
                        {"VarCharValue": "value-2"},
                        {"VarCharValue": "nested-value-2"},
                    ],
                },
            ],
            "ResultSetMetadata": {
                "ColumnInfo": [
                    {
                        "Name": "field",
                    },
                    {
                        "Name": "nested.field",
                    },
                ],
            },
        },
    }
