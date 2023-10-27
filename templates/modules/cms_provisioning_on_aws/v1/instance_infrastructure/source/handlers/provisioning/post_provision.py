# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Dict

# Third Party Libraries
import boto3
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.config import Config
from botocore.exceptions import ClientError
from dataclass_type_validator import TypeValidationError  # type: ignore

# Connected Mobility Solution on AWS
from .lib.certificate_status_enum import CertificateStatus
from .lib.dynamo_schema import ProvisionedVehicle, from_ddb_item
from .lib.dynamo_table_name_key_enum import DynamoTableNameKey

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


# This lambda is triggered by an IoT Rule listening to THING events (create, update, delete)
@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: Dict[str, Any], context: LambdaContext) -> bool:
    validate_thing_event(event)

    # Since we must listen to create and update, it is easiest to also listen to delete to avoid requiring 2 different IoT Rules
    # Because of this, we will manually ignore delete operations. We can extend the delete functionality later
    if event["operation"] != "DELETED":
        vin = event["attributes"]["vin"]
        certificate_id = event["attributes"]["certificate_id"]
        thing_name = event["thingName"]

        # Since the registration was a success, IoT has automatically activated the certificate. We update our database to match.
        set_certificate_record_status_active(vin, certificate_id)

        # Find any old INACTIVE certificates and delete them, we only need the active certificate in IoT Core.
        delete_old_certificates(vin, certificate_id, thing_name)
        return True
    return False


# pylint: disable=pointless-statement
@tracer.capture_method
def validate_thing_event(event: Dict[str, Any]) -> None:
    # In our context, this should only be triggered by the RegisterThing event, in which case the provisioning template includes the provisioned_by_template attribute
    # If this attribute is not found, the thing was created without using the provisioning_template, and we should investigate
    if (
        event.get("attributes", {}).get("provisioned_by_template", "NO_TEMPLATE")
        != os.environ["PROVISIONING_TEMPLATE_NAME"]
    ):
        logger.error(
            "IoT Thing was created or updated without using the provisioning template! ThingName: %s",
            event.get("thingName", "NAME_NOT_FOUND!"),
            exc_info=True,
        )
        raise TemplateNotUsedError(
            "IoT Thing was created or updated without using the provisioning template."
        )

    try:
        event["attributes"]["vin"]
        event["attributes"]["certificate_id"]
    except KeyError as err:
        logger.error(
            "Create thing event did not have the expected attributes from the provisioning template: %s",
            err,
            exc_info=True,
        )
        raise err


@tracer.capture_method
def set_certificate_record_status_active(vin: str, certificate_id: str) -> None:
    try:
        get_dynamodb_client().update_item(
            TableName=os.environ[
                DynamoTableNameKey.PROVISIONED_VEHICLES_TABLE_NAME.value
            ],
            Key={"vin": {"S": vin}, "certificate_id": {"S": certificate_id}},
            UpdateExpression="SET certificate_status=:activeValue",
            ExpressionAttributeValues={
                ":activeValue": {"S": CertificateStatus.ACTIVE.value}
            },
        )
    except ClientError as err:
        logger.error(
            "Error when attempting to update ProvisionedVehicles record for active certificate: %s",
            err,
            exc_info=True,
        )
        raise err


# pylint: disable=unnecessary-lambda
@tracer.capture_method
def delete_old_certificates(vin: str, certificate_id: str, thing_name: str) -> None:
    try:
        provisioned_vehicles = get_provisioned_vehicle_records(vin)
        list_certificates_iterator = (
            get_iot_client().get_paginator("list_certificates").paginate()
        )
        for certificate_page in list_certificates_iterator:
            for certificate in certificate_page["certificates"]:
                if (
                    certificate["status"] == CertificateStatus.INACTIVE.value
                    and certificate["certificateId"] != certificate_id
                    and any(
                        provisioned_vehicle.certificate_id
                        == certificate["certificateId"]
                        for provisioned_vehicle in provisioned_vehicles
                    )
                ):
                    get_iot_client().detach_thing_principal(
                        thingName=thing_name,
                        principal=certificate["certificateArn"],
                    )

                    detach_policies_from_certificate(certificate["certificateArn"])

                    get_iot_client().delete_certificate(
                        certificateId=certificate["certificateId"], forceDelete=True
                    )

                    get_dynamodb_client().update_item(
                        TableName=os.environ[
                            DynamoTableNameKey.PROVISIONED_VEHICLES_TABLE_NAME.value
                        ],
                        Key={
                            "vin": {"S": vin},
                            "certificate_id": {"S": certificate["certificateId"]},
                        },
                        UpdateExpression="SET certificate_status=:deletedValue",
                        ExpressionAttributeValues={
                            ":deletedValue": {"S": CertificateStatus.DELETED.value}
                        },
                    )
    except (KeyError, ClientError) as err:
        logger.error(
            "Error while deleting inactive certificates after a new provision: %s",
            err,
            exc_info=True,
        )
        raise err
    except (TypeValidationError, TypeError) as err:
        logger.error(
            "Error when validating ProvisionedVehicles table items: %s",
            err,
            exc_info=True,
        )
        raise err


def get_provisioned_vehicle_records(vin: str) -> list[ProvisionedVehicle]:
    provisioned_vehicles_ddb_items = get_dynamodb_client().query(
        TableName=os.environ[DynamoTableNameKey.PROVISIONED_VEHICLES_TABLE_NAME.value],
        KeyConditionExpression="vin = :vin",
        ExpressionAttributeValues={":vin": {"S": f"{vin}"}},
    )["Items"]
    provisioned_vehicles_list = list(
        map(
            lambda provisioned_vehicle_ddb_item: from_ddb_item(
                ProvisionedVehicle, provisioned_vehicle_ddb_item
            ),
            provisioned_vehicles_ddb_items,
        )
    )
    return provisioned_vehicles_list


def detach_policies_from_certificate(certificate_arn: str) -> None:
    policies = get_iot_client().list_attached_policies(
        target=certificate_arn,
        pageSize=100,  # We should really never be exceeding 1 here, so we don't need to paginate
    )["policies"]

    for policy in policies:
        get_iot_client().detach_policy(
            policyName=policy["policyName"],
            target=certificate_arn,
        )


class TemplateNotUsedError(Exception):
    pass
