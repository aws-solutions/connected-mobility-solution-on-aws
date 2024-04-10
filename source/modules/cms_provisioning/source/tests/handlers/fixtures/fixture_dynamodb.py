# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
from typing import Generator

# Third Party Libraries
import pytest
from moto import mock_aws
from mypy_boto3_dynamodb.service_resource import DynamoDBServiceResource, Table

# AWS Libraries
import boto3

# Connected Mobility Solution on AWS
from ....handlers.provisioning.function.lib.certificate_status_enum import (
    CertificateStatus,
)
from ....handlers.provisioning.function.lib.dynamo_table_name_key_enum import (
    DynamoTableNameKey,
)


@pytest.fixture(name="mock_dynamodb_resource")
def fixture_mock_dynamodb_resource() -> Generator[DynamoDBServiceResource, None, None]:
    with mock_aws():
        dynamodb = boto3.resource("dynamodb")
        yield dynamodb


@pytest.fixture(name="setup_authorized_vehicles_table_empty")
def fixture_setup_authorized_vehicles_table_empty(
    mock_dynamodb_resource: DynamoDBServiceResource,
) -> Generator[Table, None, None]:
    authorized_vehicles_table_name = os.environ[
        DynamoTableNameKey.AUTHORIZED_VEHICLES_TABLE_NAME.value
    ]

    mock_authorized_vehicles_table = mock_dynamodb_resource.create_table(
        TableName=authorized_vehicles_table_name,
        AttributeDefinitions=[
            {
                "AttributeName": "vin",
                "AttributeType": "S",
            },
        ],
        KeySchema=[
            {"AttributeName": "vin", "KeyType": "HASH"},  # Primary key
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    yield mock_authorized_vehicles_table


@pytest.fixture(name="setup_authorized_vehicles_table_provisioning_allowed")
def fixture_setup_authorized_vehicles_table_provisioning_allowed(
    setup_authorized_vehicles_table_empty: Table,
) -> Generator[Table, None, None]:
    setup_authorized_vehicles_table_empty.put_item(
        Item={
            "vin": os.environ["TEST_VIN"],
            "make": "test_make",
            "model": "test_model",
            "year": "test_year",
            "allow_provisioning": True,
        }
    )

    yield setup_authorized_vehicles_table_empty


@pytest.fixture(name="setup_authorized_vehicles_table_provisioning_denied")
def fixture_setup_authorized_vehicles_table_provisioning_denied(
    setup_authorized_vehicles_table_empty: Table,
) -> Generator[Table, None, None]:
    setup_authorized_vehicles_table_empty.put_item(
        Item={
            "vin": os.environ["TEST_VIN"],
            "make": "test_make",
            "model": "test_model",
            "year": "test_year",
            "allow_provisioning": False,
        }
    )

    yield setup_authorized_vehicles_table_empty


@pytest.fixture(name="setup_authorized_vehicles_table_invalid")
def fixture_setup_authorized_vehicles_table_invalid(
    setup_authorized_vehicles_table_empty: Table,
) -> Generator[Table, None, None]:
    setup_authorized_vehicles_table_empty.put_item(
        Item={
            "vin": os.environ["TEST_VIN"],
        }
    )

    yield setup_authorized_vehicles_table_empty


# ProvisionedVehicles setups
@pytest.fixture(name="setup_provisioned_vehicles_table_empty")
def fixture_setup_provisioned_vehicles_table_empty(
    mock_dynamodb_resource: DynamoDBServiceResource,
) -> Generator[Table, None, None]:
    provisioned_vehicles_table_name = os.environ[
        DynamoTableNameKey.PROVISIONED_VEHICLES_TABLE_NAME.value
    ]

    mock_provisioned_vehicles_table = mock_dynamodb_resource.create_table(
        TableName=provisioned_vehicles_table_name,
        AttributeDefinitions=[
            {
                "AttributeName": "vin",
                "AttributeType": "S",
            },
            {
                "AttributeName": "certificate_id",
                "AttributeType": "S",
            },
        ],
        KeySchema=[
            {"AttributeName": "vin", "KeyType": "HASH"},  # Primary key
            {"AttributeName": "certificate_id", "KeyType": "RANGE"},  # Sort key
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    yield mock_provisioned_vehicles_table


@pytest.fixture(name="setup_provisioned_vehicles_table_active")
def fixture_setup_provisioned_vehicles_table_active(
    setup_provisioned_vehicles_table_empty: Table,
) -> Generator[Table, None, None]:
    vin = os.environ["TEST_VIN"]
    setup_provisioned_vehicles_table_empty.put_item(
        Item={
            "vin": vin,
            "certificate_id": os.environ["TEST_CERTIFICATE_ID"],
            "make": "test_make",
            "model": "test_model",
            "year": "test_year",
            "region": os.environ["AWS_REGION"],
            "thing_name": f"Vehicle_{vin}",
            "certificate_status": CertificateStatus.ACTIVE.value,
            "has_vehicle_connected_once": False,
        }
    )

    yield setup_provisioned_vehicles_table_empty


@pytest.fixture(name="setup_provisioned_vehicles_table_inactive")
def fixture_setup_provisioned_vehicles_table_inactive(
    setup_provisioned_vehicles_table_empty: Table,
) -> Generator[Table, None, None]:
    vin = os.environ["TEST_VIN"]
    setup_provisioned_vehicles_table_empty.put_item(
        Item={
            "vin": vin,
            "certificate_id": os.environ["TEST_CERTIFICATE_ID"],
            "make": "test_make",
            "model": "test_model",
            "year": "test_year",
            "region": os.environ["AWS_REGION"],
            "thing_name": f"Vehicle_{vin}",
            "certificate_status": CertificateStatus.INACTIVE.value,
            "has_vehicle_connected_once": False,
        }
    )

    yield setup_provisioned_vehicles_table_empty


@pytest.fixture(name="setup_provisioned_vehicles_table_invalid")
def fixture_setup_provisioned_vehicles_table_invalid(
    setup_provisioned_vehicles_table_empty: Table,
) -> Generator[Table, None, None]:
    setup_provisioned_vehicles_table_empty.put_item(
        Item={
            "vin": os.environ["TEST_VIN"],
            "certificate_id": os.environ["TEST_CERTIFICATE_ID"],
            "invalid_key": "value",
        }
    )

    yield setup_provisioned_vehicles_table_empty
