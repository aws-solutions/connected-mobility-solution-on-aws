# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
# mypy: disable-error-code=misc
import os
from typing import Any, Dict
from unittest.mock import patch

# Third Party Libraries
import boto3
import botocore
import pytest
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.exceptions import ClientError
from moto import mock_iot  # type: ignore
from mypy_boto3_dynamodb.service_resource import Table

# Connected Mobility Solution on AWS
from ....handlers.provisioning.lib.certificate_status_enum import CertificateStatus
from ....handlers.provisioning.lib.dynamo_schema import (
    AuthorizedVehicle,
    ProvisionedVehicle,
    from_ddb_item,
)
from ....handlers.provisioning.pre_provision import (
    deactivate_existing_certificates,
    delete_denied_certificate_attempt,
    get_authorized_vehicle,
    handler,
    insert_pending_activation_provisioned_vehicles_record,
)


# Flags to assert that an API call happened
class PreProvisioningAPICallBooleans:
    UpdateCertificate = False
    DeleteCertificate = False

    @classmethod
    def reset_values(cls) -> None:
        for var in vars(PreProvisioningAPICallBooleans):
            if not callable(
                getattr(PreProvisioningAPICallBooleans, var)
            ) and not var.startswith("__"):
                setattr(PreProvisioningAPICallBooleans, var, False)

    @classmethod
    def are_all_values_false(cls) -> bool:
        are_all_values_false = True
        for var in vars(PreProvisioningAPICallBooleans):
            if not callable(
                getattr(PreProvisioningAPICallBooleans, var)
            ) and not var.startswith("__"):
                if getattr(PreProvisioningAPICallBooleans, var):
                    are_all_values_false = False
                    break
        return are_all_values_false


# pylint: disable=protected-access
orig = botocore.client.BaseClient._make_api_call  # type: ignore
# pylint: disable=too-many-return-statements, inconsistent-return-statements
def mock_make_api_call(self: Any, operation_name: str, kwarg: Any) -> Any:
    setattr(PreProvisioningAPICallBooleans, operation_name, True)
    mock_api_responses = {
        "UpdateCertificate": None,
        "DeleteCertificate": None,
    }
    if operation_name in mock_api_responses:
        return mock_api_responses[operation_name]
    return orig(self, operation_name, kwarg)


@mock_iot
def test_handler_valid_provisioning_allowed(
    setup_authorized_vehicles_table_provisioning_allowed: Table,
    setup_provisioned_vehicles_table_empty: Table,
    pre_provision_event: Dict[str, Any],
    context: LambdaContext,
) -> None:
    response = handler(pre_provision_event, context)

    assert response["allowProvisioning"]


@mock_iot
def test_handler_valid_provisioning_denied(
    setup_authorized_vehicles_table_provisioning_denied: Table,
    setup_provisioned_vehicles_table_empty: Table,
    pre_provision_event: Dict[str, Any],
    context: LambdaContext,
) -> None:
    with patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call):
        response = handler(pre_provision_event, context)

    assert not response["allowProvisioning"]


@mock_iot
def test_handler_valid_vehicle_not_found(
    setup_authorized_vehicles_table_empty: Table,
    setup_provisioned_vehicles_table_empty: Table,
    pre_provision_event: Dict[str, Any],
    context: LambdaContext,
) -> None:
    with patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call):
        response = handler(pre_provision_event, context)

    assert not response["allowProvisioning"]


def test_handler_invalid(
    pre_provision_event_invalid: Dict[str, Any],
    context: LambdaContext,
) -> None:
    response = handler(pre_provision_event_invalid, context)

    assert not response["allowProvisioning"]


@mock_iot
def test_deactivate_existing_certificates_success(
    setup_provisioned_vehicles_table_active: Table,
) -> None:
    dynamodb = boto3.client("dynamodb")
    vin = os.environ["TEST_VIN"]
    certificate_id = os.environ["TEST_CERTIFICATE_ID"]

    # Check that certificate starts active
    provisioned_vehicles_ddb_item = dynamodb.get_item(
        TableName=setup_provisioned_vehicles_table_active.table_name,
        Key={"vin": {"S": vin}, "certificate_id": {"S": certificate_id}},
    )["Item"]
    provisioned_vehicle = from_ddb_item(
        ProvisionedVehicle, provisioned_vehicles_ddb_item
    )
    assert provisioned_vehicle.certificate_status == CertificateStatus.ACTIVE.value

    assert PreProvisioningAPICallBooleans.are_all_values_false()
    with patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call):
        deactivate_existing_certificates(vin, "")
    assert PreProvisioningAPICallBooleans.UpdateCertificate is True

    # Certificate should now be inactive
    provisioned_vehicles_ddb_item = dynamodb.get_item(
        TableName=setup_provisioned_vehicles_table_active.table_name,
        Key={"vin": {"S": vin}, "certificate_id": {"S": certificate_id}},
    )["Item"]
    provisioned_vehicle = from_ddb_item(
        ProvisionedVehicle, provisioned_vehicles_ddb_item
    )
    assert provisioned_vehicle.certificate_status == CertificateStatus.INACTIVE.value


def test_deactivate_existing_certificates_client_error() -> None:
    with pytest.raises(ClientError):
        deactivate_existing_certificates(os.environ["TEST_VIN"], "")


def test_deactivate_existing_certificates_validation_error(
    setup_provisioned_vehicles_table_invalid: Table,
) -> None:
    with pytest.raises(TypeError):
        deactivate_existing_certificates(os.environ["TEST_VIN"], "")


def test_get_authorized_vehicle_success(
    setup_authorized_vehicles_table_provisioning_allowed: Table,
) -> None:
    dynamodb = boto3.client("dynamodb")
    vin = os.environ["TEST_VIN"]

    get_authorized_vehicle(vin)

    authorized_vehicle_ddb_item = dynamodb.get_item(
        TableName=setup_authorized_vehicles_table_provisioning_allowed.table_name,
        Key={
            "vin": {"S": vin},
        },
    )["Item"]
    authorized_vehicle = from_ddb_item(AuthorizedVehicle, authorized_vehicle_ddb_item)

    assert authorized_vehicle.vin == vin


def test_get_authorized_vehicle_not_found(
    setup_authorized_vehicles_table_empty: Table,
) -> None:
    authorized_vehicle = get_authorized_vehicle(os.environ["TEST_VIN"])
    assert authorized_vehicle is None


def test_get_authorized_vehicle_validation_error(
    setup_authorized_vehicles_table_invalid: Table,
) -> None:
    with pytest.raises(TypeError):
        get_authorized_vehicle(os.environ["TEST_VIN"])


def test_get_authorized_vehicle_client_error() -> None:
    with pytest.raises(ClientError):
        get_authorized_vehicle(os.environ["TEST_VIN"])


def test_insert_pending_activation_provisioned_vehicles_record_vehicle_found(
    authorized_vehicle_allowed: AuthorizedVehicle,
    setup_provisioned_vehicles_table_empty: Table,
) -> None:
    vin = os.environ["TEST_VIN"]
    certificate_id = os.environ["TEST_CERTIFICATE_ID"]
    dynamodb = boto3.client("dynamodb")

    # Check that table does not contain this record
    try:
        dynamodb.get_item(
            TableName=setup_provisioned_vehicles_table_empty.table_name,
            Key={"vin": {"S": vin}, "certificate_id": {"S": certificate_id}},
        )["Item"]
    except KeyError:
        pass

    insert_pending_activation_provisioned_vehicles_record(
        authorized_vehicle_allowed, vin, certificate_id
    )

    # Check that table now contains record in PENDING_ACTIVATION state
    provisioned_vehicles_ddb_item = dynamodb.get_item(
        TableName=setup_provisioned_vehicles_table_empty.table_name,
        Key={"vin": {"S": vin}, "certificate_id": {"S": certificate_id}},
    )["Item"]
    provisioned_vehicle = from_ddb_item(
        ProvisionedVehicle, provisioned_vehicles_ddb_item
    )
    assert (
        provisioned_vehicle.certificate_status
        == CertificateStatus.PENDING_ACTIVATION.value
    )


def test_insert_pending_activation_provisioned_vehicles_record_vehicle_not_found(
    setup_provisioned_vehicles_table_empty: Table,
) -> None:
    vin = os.environ["TEST_VIN"]
    certificate_id = os.environ["TEST_CERTIFICATE_ID"]
    dynamodb = boto3.client("dynamodb")

    # Check that table does not contain this record
    try:
        dynamodb.get_item(
            TableName=setup_provisioned_vehicles_table_empty.table_name,
            Key={"vin": {"S": vin}, "certificate_id": {"S": certificate_id}},
        )["Item"]
    except KeyError:
        pass

    authorized_vehicle = None
    insert_pending_activation_provisioned_vehicles_record(
        authorized_vehicle, vin, certificate_id
    )

    # Check that table now contains record in PENDING_ACTIVATION state
    provisioned_vehicles_ddb_item = dynamodb.get_item(
        TableName=setup_provisioned_vehicles_table_empty.table_name,
        Key={"vin": {"S": vin}, "certificate_id": {"S": certificate_id}},
    )["Item"]
    provisioned_vehicle = from_ddb_item(
        ProvisionedVehicle, provisioned_vehicles_ddb_item
    )

    assert (
        provisioned_vehicle.certificate_status
        == CertificateStatus.PENDING_ACTIVATION.value
    )


def test_insert_pending_activation_provisioned_vehicles_record_client_error(
    authorized_vehicle_allowed: AuthorizedVehicle,
) -> None:
    vin = os.environ["TEST_VIN"]
    certificate_id = os.environ["TEST_CERTIFICATE_ID"]

    with pytest.raises(ClientError):
        insert_pending_activation_provisioned_vehicles_record(
            authorized_vehicle_allowed, vin, certificate_id
        )


def test_delete_denied_certificate_attempt_success(
    setup_provisioned_vehicles_table_inactive: Table,
) -> None:
    vin = os.environ["TEST_VIN"]
    certificate_id = os.environ["TEST_CERTIFICATE_ID"]
    dynamodb = boto3.client("dynamodb")

    # Check that record starts in INACTIVE state
    provisioned_vehicles_ddb_item = dynamodb.get_item(
        TableName=setup_provisioned_vehicles_table_inactive.table_name,
        Key={"vin": {"S": vin}, "certificate_id": {"S": certificate_id}},
    )["Item"]
    provisioned_vehicle = from_ddb_item(
        ProvisionedVehicle, provisioned_vehicles_ddb_item
    )

    assert provisioned_vehicle.certificate_status == CertificateStatus.INACTIVE.value

    assert PreProvisioningAPICallBooleans.are_all_values_false()
    with patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call):
        delete_denied_certificate_attempt(vin, certificate_id)
    assert PreProvisioningAPICallBooleans.DeleteCertificate is True

    # Check that record is now in DELETED state
    provisioned_vehicles_ddb_item = dynamodb.get_item(
        TableName=setup_provisioned_vehicles_table_inactive.table_name,
        Key={"vin": {"S": vin}, "certificate_id": {"S": certificate_id}},
    )["Item"]
    provisioned_vehicle = from_ddb_item(
        ProvisionedVehicle, provisioned_vehicles_ddb_item
    )

    assert provisioned_vehicle.certificate_status == CertificateStatus.DELETED.value


def test_delete_denied_certificate_attempt_client_error() -> None:
    vin = os.environ["TEST_VIN"]
    certificate_id = os.environ["TEST_CERTIFICATE_ID"]

    with pytest.raises(ClientError):
        delete_denied_certificate_attempt(vin, certificate_id)
