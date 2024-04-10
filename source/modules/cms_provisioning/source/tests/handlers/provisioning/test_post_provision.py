# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0


# Standard Library
# mypy: disable-error-code=misc
import os
from typing import Any, Dict
from unittest.mock import patch

# Third Party Libraries
import pytest
from mypy_boto3_dynamodb.service_resource import Table

# AWS Libraries
import boto3
import botocore
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.exceptions import ClientError

# Connected Mobility Solution on AWS
from ....handlers.provisioning.function.lib.certificate_status_enum import (
    CertificateStatus,
)
from ....handlers.provisioning.function.lib.dynamo_schema import (
    ProvisionedVehicle,
    from_ddb_item,
)
from ....handlers.provisioning.function.post_provision import (
    TemplateNotUsedError,
    delete_old_certificates,
    handler,
    set_certificate_record_status_active,
    validate_thing_event,
)


# Flags to assert that an API call happened
class PostProvisioningAPICallBooleans:
    DeleteCertificate = False
    DetachThingPrincipal = False
    ListAttachedPolicies = False
    DetachPolicy = False
    ListCertificates = False

    @classmethod
    def reset_values(cls) -> None:
        for var in vars(PostProvisioningAPICallBooleans):
            if not callable(
                getattr(PostProvisioningAPICallBooleans, var)
            ) and not var.startswith("__"):
                setattr(PostProvisioningAPICallBooleans, var, False)

    @classmethod
    def are_all_values_false(cls) -> bool:
        are_all_values_false = True
        for var in vars(PostProvisioningAPICallBooleans):
            if not callable(
                getattr(PostProvisioningAPICallBooleans, var)
            ) and not var.startswith("__"):
                if getattr(PostProvisioningAPICallBooleans, var):
                    are_all_values_false = False
                    break
        return are_all_values_false


# pylint: disable=protected-access
orig = botocore.client.BaseClient._make_api_call  # type: ignore
# pylint: disable=too-many-return-statements, inconsistent-return-statements
def mock_make_api_call(self: Any, operation_name: str, kwarg: Any) -> Any:
    setattr(PostProvisioningAPICallBooleans, operation_name, True)
    mock_api_responses = {
        "DeleteCertificate": None,
        "DetachThingPrincipal": None,
        "ListAttachedPolicies": {"policies": [{"policyName": "test-policy-name"}]},
        "DetachPolicy": None,
        "ListCertificates": {
            "certificates": [
                {
                    "status": CertificateStatus.INACTIVE.value,
                    "certificateId": os.environ["TEST_CERTIFICATE_ID"],
                    "certificateArn": "test_arn",
                }
            ]
        },
    }
    if operation_name in mock_api_responses:
        return mock_api_responses[operation_name]
    return orig(self, operation_name, kwarg)


def test_handler_valid_event(
    post_provision_event: Dict[str, Any],
    context: LambdaContext,
    setup_provisioned_vehicles_table_inactive: Table,
) -> None:
    with patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call):
        assert handler(post_provision_event, context)


def test_handler_deleted_event(
    post_provision_event_deleted_event: Dict[str, Any], context: LambdaContext
) -> None:
    with patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call):
        assert not handler(post_provision_event_deleted_event, context)


def test_validate_thing_event_valid_event(post_provision_event: Dict[str, Any]) -> None:
    validate_thing_event(post_provision_event)


def test_validate_thing_event_template_not_used(
    post_provision_event_no_template: Dict[str, Any]
) -> None:
    with pytest.raises(TemplateNotUsedError):
        validate_thing_event(post_provision_event_no_template)


def test_validate_thing_event_template_missing_attributes(
    post_provision_event_no_attributes: Dict[str, Any]
) -> None:
    with pytest.raises(KeyError):
        validate_thing_event(post_provision_event_no_attributes)


def test_set_certificate_record_status_active_success(
    setup_provisioned_vehicles_table_inactive: Table,
) -> None:
    vin = os.environ["TEST_VIN"]
    certificate_id = os.environ["TEST_CERTIFICATE_ID"]
    dynamodb = boto3.client("dynamodb")

    # Check that certificate starts INACTIVE
    provisioned_vehicles_ddb_item = dynamodb.get_item(
        TableName=setup_provisioned_vehicles_table_inactive.table_name,
        Key={"vin": {"S": vin}, "certificate_id": {"S": certificate_id}},
    )["Item"]
    provisioned_vehicle: ProvisionedVehicle = from_ddb_item(
        ProvisionedVehicle, provisioned_vehicles_ddb_item
    )

    assert provisioned_vehicle.certificate_status == CertificateStatus.INACTIVE.value

    set_certificate_record_status_active(vin, certificate_id)

    # Check that certificate is now ACTIVE
    provisioned_vehicles_ddb_item = dynamodb.get_item(
        TableName=setup_provisioned_vehicles_table_inactive.table_name,
        Key={"vin": {"S": vin}, "certificate_id": {"S": certificate_id}},
    )["Item"]
    provisioned_vehicle = from_ddb_item(
        ProvisionedVehicle, provisioned_vehicles_ddb_item
    )

    assert provisioned_vehicle.certificate_status == CertificateStatus.ACTIVE.value


def test_set_certificate_record_status_active_client_error() -> None:
    vin = os.environ["TEST_VIN"]
    certificate_id = os.environ["TEST_CERTIFICATE_ID"]

    with pytest.raises(ClientError):
        set_certificate_record_status_active(vin, certificate_id)


def test_delete_old_certificates_success(
    setup_provisioned_vehicles_table_inactive: Table,
) -> None:
    vin = os.environ["TEST_VIN"]
    certificate_id = os.environ["TEST_CERTIFICATE_ID"]
    new_certificate_id = "certificate_not_equal_to_environment_certificate"
    thing_name = f"Vehicle_{vin}"
    dynamodb = boto3.client("dynamodb")

    # Check that certificate starts INACTIVE
    provisioned_vehicles_ddb_item = dynamodb.get_item(
        TableName=setup_provisioned_vehicles_table_inactive.table_name,
        Key={"vin": {"S": vin}, "certificate_id": {"S": certificate_id}},
    )["Item"]
    provisioned_vehicle: ProvisionedVehicle = from_ddb_item(
        ProvisionedVehicle, provisioned_vehicles_ddb_item
    )

    assert provisioned_vehicle.certificate_status == CertificateStatus.INACTIVE.value

    # This function deletes all OTHER inactive certificates when a new certificate/thing is created
    # So we need some certificate_id not equal to the one we are using in our mock db table to be the "new certificate"
    assert PostProvisioningAPICallBooleans.are_all_values_false()
    with patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call):
        delete_old_certificates(vin, new_certificate_id, thing_name)
    assert PostProvisioningAPICallBooleans.ListCertificates is True
    assert PostProvisioningAPICallBooleans.DetachThingPrincipal is True
    assert PostProvisioningAPICallBooleans.ListAttachedPolicies is True
    assert PostProvisioningAPICallBooleans.DetachPolicy is True
    assert PostProvisioningAPICallBooleans.DeleteCertificate is True

    # Check that certificate is now DELETED
    provisioned_vehicles_ddb_item = dynamodb.get_item(
        TableName=setup_provisioned_vehicles_table_inactive.table_name,
        Key={"vin": {"S": vin}, "certificate_id": {"S": certificate_id}},
    )["Item"]
    provisioned_vehicle_deleted: ProvisionedVehicle = from_ddb_item(
        ProvisionedVehicle, provisioned_vehicles_ddb_item
    )

    assert (
        provisioned_vehicle_deleted.certificate_status
        == CertificateStatus.DELETED.value
    )


def test_delete_old_certificates_client_error() -> None:
    vin = os.environ["TEST_VIN"]
    new_certificate_id = os.environ["TEST_CERTIFICATE_ID"]
    thing_name = f"Vehicle_{vin}"

    with pytest.raises(ClientError):
        delete_old_certificates(vin, new_certificate_id, thing_name)


def test_delete_old_certificates_type_error(
    setup_provisioned_vehicles_table_invalid: Table,
) -> None:
    vin = os.environ["TEST_VIN"]
    new_certificate_id = os.environ["TEST_CERTIFICATE_ID"]
    thing_name = f"Vehicle_{vin}"

    with pytest.raises(TypeError):
        with patch("botocore.client.BaseClient._make_api_call", new=mock_make_api_call):
            delete_old_certificates(vin, new_certificate_id, thing_name)
