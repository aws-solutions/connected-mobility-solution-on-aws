# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Dict, Optional

# Third Party Libraries
import boto3
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.config import Config
from botocore.exceptions import ClientError
from dataclass_type_validator import TypeValidationError  # type: ignore

# Connected Mobility Solution on AWS
from .lib.certificate_status_enum import CertificateStatus
from .lib.dynamo_schema import (
    AuthorizedVehicle,
    ProvisionedVehicle,
    from_ddb_item,
    to_ddb_item,
)
from .lib.dynamo_table_name_key_enum import DynamoTableNameKey
from .lib.validators import sanitize_vin

if TYPE_CHECKING:
    # Third Party Libraries
    from mypy_boto3_dynamodb.client import DynamoDBClient
    from mypy_boto3_iot.client import IoTClient
else:
    DynamoDBClient = object
    IoTClient = object


tracer = Tracer()
logger = Logger()


@lru_cache(maxsize=128)
def get_dynamodb_client() -> DynamoDBClient:
    return boto3.client(
        "dynamodb", config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"])
    )


@lru_cache(maxsize=128)
def get_iot_client() -> IoTClient:
    return boto3.client(
        "iot", config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"])
    )


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    response = {"allowProvisioning": False, "parameterOverrides": {}}
    certificate_id = event["certificateId"]

    try:
        vin = sanitize_vin(event["parameters"]["vin"])
    except KeyError as err:
        logger.error(
            "Error when attempting to provision vehicle. Template parameters must include a vin: %s",
            err,
            exc_info=True,
        )
        return response

    # If this vehicle has already been provisioned, an Active or Pending certificate may already exist. If so, we want to deactivate them.
    deactivate_existing_certificates(vin, certificate_id)

    authorized_vehicle = get_authorized_vehicle(vin)
    response["allowProvisioning"] = (
        authorized_vehicle.allow_provisioning
        if authorized_vehicle is not None
        else False
    )

    # We will keep an active record of the vin/certificate combo and it's status, which right now is PENDING_ACTIVATION
    insert_pending_activation_provisioned_vehicles_record(
        authorized_vehicle, vin, certificate_id
    )

    # If provisioning was denied, we no longer need the certificate, and we will also update the ProvisionedVehicle table to reflect this deletion
    if not response["allowProvisioning"]:
        delete_denied_certificate_attempt(vin, certificate_id)

    return response


@tracer.capture_method
def deactivate_existing_certificates(vin: str, certificate_id: str) -> None:
    try:
        provisioned_vehicles_ddb_items = get_dynamodb_client().query(
            TableName=os.environ[
                DynamoTableNameKey.PROVISIONED_VEHICLES_TABLE_NAME.value
            ],
            KeyConditionExpression="vin = :vin",
            ExpressionAttributeValues={":vin": {"S": f"{vin}"}},
        )["Items"]
        for provisioned_vehicles_ddb_item in provisioned_vehicles_ddb_items:
            provisioned_vehicle = from_ddb_item(
                ProvisionedVehicle, provisioned_vehicles_ddb_item
            )
            if (
                provisioned_vehicle.certificate_status
                in (
                    CertificateStatus.ACTIVE.value,
                    CertificateStatus.PENDING_ACTIVATION.value,
                )
                and provisioned_vehicle.certificate_id != certificate_id
            ):
                get_iot_client().update_certificate(
                    certificateId=provisioned_vehicle.certificate_id,
                    newStatus=CertificateStatus.INACTIVE.value,
                )
                get_dynamodb_client().update_item(
                    TableName=os.environ[
                        DynamoTableNameKey.PROVISIONED_VEHICLES_TABLE_NAME.value
                    ],
                    Key={
                        "vin": {"S": vin},
                        "certificate_id": {"S": provisioned_vehicle.certificate_id},
                    },
                    UpdateExpression="SET certificate_status=:inactiveValue",
                    ExpressionAttributeValues={
                        ":inactiveValue": {"S": CertificateStatus.INACTIVE.value}
                    },
                )
    except (TypeValidationError, TypeError) as err:
        logger.error(
            "Error when validating ProvisionedVehicles table items: %s",
            err,
            exc_info=True,
        )
        raise err
    except (KeyError, ClientError) as err:
        logger.error(
            "Error when retrieving/updating ProvisionedVehicles table items: %s",
            err,
            exc_info=True,
        )
        raise err


@tracer.capture_method
def get_authorized_vehicle(vin: str) -> Optional[AuthorizedVehicle]:
    authorized_vehicle = None
    try:
        authorized_vehicle_ddb_item = get_dynamodb_client().get_item(
            TableName=os.environ[
                DynamoTableNameKey.AUTHORIZED_VEHICLES_TABLE_NAME.value
            ],
            Key={
                "vin": {"S": vin},
            },
        )["Item"]
        authorized_vehicle = from_ddb_item(
            AuthorizedVehicle, authorized_vehicle_ddb_item
        )
    except KeyError:  # If a record is not found, get_item return will not have an "Item" element, and ["Item"] will throw a KeyError
        logger.info(
            "Vehicle with vin %s was not found in the AuthorizedVehicles table. Provisioning not allowed.",
            vin,
        )
    except (TypeValidationError, TypeError) as err:
        logger.error(
            "Error when validating AuthorizedVehicle item: %s", err, exc_info=True
        )
        raise err
    except ClientError as err:
        logger.error(
            "Error when retrieving AuthorizedVehicles table item: %s",
            err,
            exc_info=True,
        )
        raise err
    return authorized_vehicle


@tracer.capture_method
def insert_pending_activation_provisioned_vehicles_record(
    authorized_vehicle: Optional[AuthorizedVehicle], vin: str, certificate_id: str
) -> None:
    try:
        if authorized_vehicle is not None:
            provisioned_vehicle = ProvisionedVehicle(
                vin=vin,
                certificate_id=certificate_id,
                make=authorized_vehicle.make,
                model=authorized_vehicle.model,
                year=authorized_vehicle.year,
                region=os.environ["AWS_REGION"],
                thing_name=f"Vehicle_{vin}",
                certificate_status=CertificateStatus.PENDING_ACTIVATION.value,
                has_vehicle_connected_once=False,
            )
            get_dynamodb_client().put_item(
                TableName=os.environ[
                    DynamoTableNameKey.PROVISIONED_VEHICLES_TABLE_NAME.value
                ],
                Item=to_ddb_item(provisioned_vehicle),
            )
        else:  # If AuthorizedVehicle record is not found, we don't have vehicle information outside of vin
            provisioned_vehicle = ProvisionedVehicle(
                vin=vin,
                certificate_id=certificate_id,
                make="AUTHORIZED_VEHICLE_NOT_FOUND",
                model="AUTHORIZED_VEHICLE_NOT_FOUND",
                year="AUTHORIZED_VEHICLE_NOT_FOUND",
                region=os.environ["AWS_REGION"],
                thing_name=f"Vehicle_{vin}",
                certificate_status=CertificateStatus.PENDING_ACTIVATION.value,
                has_vehicle_connected_once=False,
            )
            get_dynamodb_client().put_item(
                TableName=os.environ[
                    DynamoTableNameKey.PROVISIONED_VEHICLES_TABLE_NAME.value
                ],
                Item=to_ddb_item(provisioned_vehicle),
            )
    except (ClientError) as err:
        logger.error(
            "Error when inserting ProvisionedVehicle record: %s", err, exc_info=True
        )
        raise err


@tracer.capture_method
def delete_denied_certificate_attempt(vin: str, certificate_id: str) -> None:
    try:
        get_iot_client().delete_certificate(
            certificateId=certificate_id, forceDelete=True
        )
        get_dynamodb_client().update_item(
            TableName=os.environ[
                DynamoTableNameKey.PROVISIONED_VEHICLES_TABLE_NAME.value
            ],
            Key={
                "vin": {"S": vin},
                "certificate_id": {"S": certificate_id},
            },
            UpdateExpression="SET certificate_status=:deletedValue",
            ExpressionAttributeValues={
                ":deletedValue": {"S": CertificateStatus.DELETED.value}
            },
        )
    except (ClientError) as err:
        logger.error(
            "Error when attempting to delete certificate for vehicle not allowed to provision: %s",
            err,
            exc_info=True,
        )
        raise err
