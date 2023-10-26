# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0


# Standard Library
# mypy: disable-error-code=misc
import os
from typing import Any, Dict

# Third Party Libraries
import boto3
import pytest
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.exceptions import ClientError
from mypy_boto3_dynamodb.service_resource import Table

# Connected Mobility Solution on AWS
from ....handlers.provisioning.initial_connection import handler
from ....handlers.provisioning.lib.dynamo_schema import (
    ProvisionedVehicle,
    from_ddb_item,
)


def test_handler_success(
    initial_connection_event_valid: Dict[str, Any],
    context: LambdaContext,
    setup_provisioned_vehicles_table_active: Table,
) -> None:
    vin = os.environ["TEST_VIN"]
    certificate_id = os.environ["TEST_CERTIFICATE_ID"]
    dynamodb = boto3.client("dynamodb")

    # Check that certificate starts with has_vehicle_connected_once False
    provisioned_vehicles_ddb_item = dynamodb.get_item(
        TableName=setup_provisioned_vehicles_table_active.table_name,
        Key={"vin": {"S": vin}, "certificate_id": {"S": certificate_id}},
    )["Item"]
    provisioned_vehicle = from_ddb_item(
        ProvisionedVehicle, provisioned_vehicles_ddb_item
    )
    assert not provisioned_vehicle.has_vehicle_connected_once

    handler(initial_connection_event_valid, context)

    # Check that certificate now has_vehicle_connected_once True
    provisioned_vehicles_ddb_item = dynamodb.get_item(
        TableName=setup_provisioned_vehicles_table_active.table_name,
        Key={"vin": {"S": vin}, "certificate_id": {"S": certificate_id}},
    )["Item"]
    provisioned_vehicle = from_ddb_item(
        ProvisionedVehicle, provisioned_vehicles_ddb_item
    )
    assert provisioned_vehicle.has_vehicle_connected_once


def test_handler_key_error(
    initial_connection_event_invalid: Dict[str, Any],
    context: LambdaContext,
    setup_provisioned_vehicles_table_active: Table,
) -> None:
    with pytest.raises(KeyError):
        handler(initial_connection_event_invalid, context)


def test_handler_client_error(
    initial_connection_event_valid: Dict[str, Any],
    context: LambdaContext,
) -> None:
    with pytest.raises(ClientError):
        handler(initial_connection_event_valid, context)
