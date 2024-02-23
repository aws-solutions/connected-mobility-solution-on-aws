# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Generator

# Third Party Libraries
import boto3
import pytest
from moto import mock_aws  # type: ignore


@pytest.fixture(name="dynamodb_table")
def fixture_dynamodb_table() -> Generator[str, None, None]:
    with mock_aws():
        table_name = "test_table"
        table = boto3.resource("dynamodb")
        table.create_table(
            AttributeDefinitions=[
                {
                    "AttributeName": "id",
                    "AttributeType": "S",
                },
            ],
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "id", "KeyType": "HASH"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        table.Table(table_name).put_item(
            Item={
                "id": "test_id_1",
                "test_val": "test_val_1",
            }
        )
        table.Table(table_name).put_item(
            Item={
                "id": "test_id_2",
                "test_val": "test_val_2",
            }
        )
        yield table_name
