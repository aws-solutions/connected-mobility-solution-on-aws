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

# Connected Mobility Solution on AWS
from .lib.dynamo_table_name_key_enum import DynamoTableNameKey

if TYPE_CHECKING:
    # Third Party Libraries
    from mypy_boto3_dynamodb.client import DynamoDBClient
else:
    DynamoDBClient = object


tracer = Tracer()
logger = Logger()


@lru_cache(maxsize=128)
def get_dynamodb_client() -> DynamoDBClient:
    return boto3.client(
        "dynamodb", config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"])
    )


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: Dict[str, Any], context: LambdaContext) -> None:
    try:
        get_dynamodb_client().update_item(
            TableName=os.environ[
                DynamoTableNameKey.PROVISIONED_VEHICLES_TABLE_NAME.value
            ],
            Key={
                "vin": {"S": event["vin"]},
                "certificate_id": {"S": event["certificate_id"]},
            },
            UpdateExpression="SET has_vehicle_connected_once=:trueValue",
            ExpressionAttributeValues={":trueValue": {"BOOL": True}},
        )
    except KeyError as err:
        logger.error(
            "vehicleactive topic publish did not include the necessary payload parameters: %s",
            err,
            exc_info=True,
        )
        raise err
    except ClientError as err:
        logger.error(
            "Error when attempting to update ProvisionedVehicles record for initial vehicle connection: %s",
            err,
            exc_info=True,
        )
        raise err
