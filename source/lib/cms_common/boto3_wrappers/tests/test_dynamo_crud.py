# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any, Dict

# Third Party Libraries
import pytest
from moto import mock_aws

# AWS Libraries
import boto3

# Connected Mobility Solution on AWS
from ..dynamo_crud import DynHelpers


@mock_aws
def test_dyn_resource() -> None:
    dynamo = DynHelpers.dyn_resource()
    assert dynamo and DynHelpers.dynamo_object


def test_get_all(dynamodb_table: str) -> None:
    items = DynHelpers.get_all(table=dynamodb_table, Limit=1)
    assert len(items) == 2


def test_put_item(dynamodb_table: str) -> None:
    new_item = {
        "id": "test_put",
        "test_val": "test_val_put",
    }
    DynHelpers.put_item(dynamodb_table, new_item)

    dynamodb = boto3.resource("dynamodb")
    item = dynamodb.Table(dynamodb_table).get_item(Key={"id": new_item["id"]})
    assert item["Item"]


def test_get_item(dynamodb_table: str) -> None:
    response = DynHelpers.get_item(dynamodb_table, {"id": "test_id_1"})
    assert response


def test_update_item(dynamodb_table: str) -> None:
    item: Dict[str, Any] = {"id": "test_id_1"}
    updated_test_val = "test_val_1_updated"

    DynHelpers.update_item(
        dynamodb_table,
        item,
        "SET test_val = :updated_test_val",
        {":updated_test_val": updated_test_val},
    )

    dynamodb = boto3.resource("dynamodb")
    item = dynamodb.Table(dynamodb_table).get_item(Key={"id": item["id"]})  # type: ignore[assignment]

    assert item["Item"]["test_val"] == updated_test_val


def test_delete_item(dynamodb_table: str) -> None:
    DynHelpers.get_item(dynamodb_table, {"id": "test_id_1"})
    DynHelpers.delete_item(dynamodb_table, {"id": "test_id_1"})
    with pytest.raises(KeyError):
        DynHelpers.get_item(dynamodb_table, {"id": "test_id_1"})


def test_dyn_batch_get(dynamodb_table: str) -> None:
    keys = ["test_id_1", "test_id_2"]
    batch_keys = {dynamodb_table: {"Keys": [{"id": key} for key in keys]}}
    response = DynHelpers.dyn_batch_get(batch_keys)
    assert len(response[dynamodb_table]) == 2


def test_dyn_scan(dynamodb_table: str) -> None:
    items = DynHelpers.dyn_scan(table=dynamodb_table, Limit=1)
    assert len(list(items)) == 2


def test_dyn_batch_write(dynamodb_table: str) -> None:
    items = [
        {
            "operation": "PUT",
            "item": {
                "id": "test_id_3",
                "test_val": "test_val_3",
            },
        },
        {
            "operation": "PUT",
            "item": {
                "id": "test_id_4",
                "test_val": "test_val_4",
            },
        },
    ]
    DynHelpers.dyn_batch_write(dynamodb_table, items)
    response = DynHelpers.dyn_batch_get(
        {dynamodb_table: {"Keys": [{"id": key} for key in ["test_id_3", "test_id_4"]]}}
    )
    assert len(response[dynamodb_table]) == 2
    assert response[dynamodb_table][0]["id"] == "test_id_3"
    assert response[dynamodb_table][1]["id"] == "test_id_4"
    assert response[dynamodb_table][0]["test_val"] == "test_val_3"
    assert response[dynamodb_table][1]["test_val"] == "test_val_4"


def test_dyn_batch_delete(dynamodb_table: str) -> None:
    items = [
        {
            "operation": "DELETE",
            "key": {"id": "test_id_3"},
        },
        {
            "operation": "DELETE",
            "key": {"id": "test_id_4"},
        },
    ]

    DynHelpers.dyn_batch_write(dynamodb_table, items)
    response = DynHelpers.dyn_batch_get(
        {dynamodb_table: {"Keys": [{"id": key} for key in ["test_id_3", "test_id_4"]]}}
    )
    assert len(response[dynamodb_table]) == 0


def test_dyn_query(dynamodb_table: str) -> None:
    response = DynHelpers.dyn_query(
        table_name=dynamodb_table,
        key_condition_expression="id=:id",
        projection_expression="#I, #V",
        expression_attribute_names={
            "#I": "id",
            "#V": "test_val",
        },
        expression_attribute_values={":id": "test_id_1"},
    )
    assert len(response) == 1
    assert response[0]["id"] == "test_id_1"
    assert response[0]["test_val"] == "test_val_1"
