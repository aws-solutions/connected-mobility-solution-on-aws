# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json
import os
import time
from enum import Enum
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Dict
from uuid import uuid4

# Third Party Libraries
import requests

# AWS Libraries
import boto3
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.config import Config

# CMS Common Library
from cms_common.boto3_wrappers.dynamo_crud import DynHelpers

tracer = Tracer()
logger = Logger()

if TYPE_CHECKING:
    # Third Party Libraries
    from mypy_boto3_cognito_idp.client import CognitoIdentityProviderClient
    from mypy_boto3_iot.client import IoTClient
    from mypy_boto3_s3 import S3Client

else:
    CognitoIdentityProviderClient = object
    IoTClient = object
    S3Client = object


@lru_cache(maxsize=128)
def get_s3_client() -> S3Client:
    return boto3.client(
        "s3", config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"])
    )


@lru_cache(maxsize=128)
def get_iot_client() -> IoTClient:
    return boto3.client(
        "iot", config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"])
    )


@lru_cache(maxsize=128)
def get_cognito_client() -> CognitoIdentityProviderClient:
    return boto3.client(
        "cognito-idp", config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"])
    )


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    response = {"Status": CustomResourceTypes.StatusTypes.SUCCESS.value, "Data": {}}

    resource_map = {
        CustomResourceTypes.ResourceTypes.DETACH_IOT_POLICY.value: detach_iot_policy,
        CustomResourceTypes.ResourceTypes.CREATE_UUID.value: create_uuid,
        CustomResourceTypes.ResourceTypes.CREATE_CONFIG.value: create_console_config,
        CustomResourceTypes.ResourceTypes.CREATE_USERPOOL_USER.value: create_userpool_user,
        CustomResourceTypes.ResourceTypes.COPY_TEMPLATE.value: copy_template_to_table,
        CustomResourceTypes.ResourceTypes.CREATE_IOT_THING_GROUP.value: create_iot_thing_group,
    }

    retry = 20
    while retry:
        try:
            response["Data"] = resource_map[event["ResourceProperties"]["Resource"]](event)  # type: ignore
            retry = 0
        except Exception as exception:  # pylint: disable=broad-exception-caught
            # Wrap all exceptions so CloudFormation doesn't hang
            logger.error("CustomResource error; retries left %s: %s", retry, exception)
            time.sleep(1 * retry)
            retry -= 1

    send_cloud_formation_response(
        event,
        response,
        f"See the details in CloudWatch Log Stream: {context.log_stream_name}",
    )

    return response


@tracer.capture_method
def send_cloud_formation_response(
    event: Dict[str, Any], response: Dict[str, Any], reason: str
) -> None:
    response_body = {
        "Status": response["Status"],
        "Reason": reason,
        "PhysicalResourceId": event["LogicalResourceId"],
        "StackId": event["StackId"],
        "RequestId": event["RequestId"],
        "LogicalResourceId": event["LogicalResourceId"],
        "Data": response["Data"],
    }

    logger.info("response", extra={"response_body": response_body})

    headers = {"Content-Type": "application/json"}

    requests.put(
        event["ResponseURL"],
        data=json.dumps(response_body),
        headers=headers,
        timeout=60,
    )


# ---------------------------------------------------- CustomResources ----------------------------------------------------
@tracer.capture_method
def create_uuid(event: Dict[str, Any]) -> Dict[str, str]:
    uuid = str(uuid4())
    return {
        "UUID": uuid,
        "UNIQUE_SUFFIX": "".join(uuid.split("-")),
        "REDUCED_STACK_NAME": event["ResourceProperties"]["StackName"][:10],
    }


@tracer.capture_method
def create_console_config(event: Dict[str, Any]) -> Dict[str, str]:
    if event["RequestType"] in [
        CustomResourceTypes.RequestTypes.CREATE.value,
        CustomResourceTypes.RequestTypes.UPDATE.value,
    ]:
        s3_obj = (
            f"const config = {json.loads(event['ResourceProperties']['configObj'])};"
        )
        get_s3_client().put_object(
            Body=s3_obj,
            Bucket=event["ResourceProperties"]["DestinationBucket"],
            Key=event["ResourceProperties"]["ConfigFileName"],
            ContentType="application/javascript",
        )
        logger.info(
            "created s3 obj at %s",
            event["ResourceProperties"]["DestinationBucket"],
        )
        logger.info("s3 obj: %s", s3_obj)

    return {"Bucket": event["ResourceProperties"]["DestinationBucket"]}


@tracer.capture_method
def detach_iot_policy(event: Dict[str, Any]) -> None:
    if event["RequestType"] == CustomResourceTypes.RequestTypes.DELETE.value:
        iot_targets = get_iot_client().list_targets_for_policy(
            policyName=event["ResourceProperties"]["IoTPolicyName"]
        )

        for target in iot_targets["targets"]:
            get_iot_client().detach_principal_policy(
                policyName=event["ResourceProperties"]["IoTPolicyName"],
                principal=target,
            )

            logger.info(
                "%s is detached from %s",
                target,
                event["ResourceProperties"]["IoTPolicyName"],
            )


@tracer.capture_method
def create_userpool_user(event: Dict[str, Any]) -> None:
    if event["RequestType"] in [
        CustomResourceTypes.RequestTypes.CREATE.value,
        CustomResourceTypes.RequestTypes.UPDATE.value,
    ]:
        user_pool_id = event["ResourceProperties"]["UserpoolId"]
        username = event["ResourceProperties"]["Username"]
        user_attributes = event["ResourceProperties"]["UserAttributes"]
        desired_delivery_mediums = event["ResourceProperties"]["DesiredDeliveryMediums"]
        force_alias_creation = (
            event["ResourceProperties"]["ForceAliasCreation"] == "true"
        )
        try:
            get_cognito_client().admin_create_user(
                UserPoolId=user_pool_id,
                Username=username,
                UserAttributes=user_attributes,
                ForceAliasCreation=force_alias_creation,
                DesiredDeliveryMediums=desired_delivery_mediums,
            )
        except get_cognito_client().exceptions.UsernameExistsException:
            # stack was probably executed before or user was added manually
            ...


@tracer.capture_method
def copy_template_to_table(event: Dict[str, Any]) -> None:
    if event["RequestType"] in [
        CustomResourceTypes.RequestTypes.CREATE.value,
        CustomResourceTypes.RequestTypes.UPDATE.value,
    ]:
        item = json.loads(event["ResourceProperties"]["Template"])
        table_name = event["ResourceProperties"]["TableName"]
        DynHelpers.put_item(table_name, item)


@tracer.capture_method
def create_iot_thing_group(event: Dict[str, Any]) -> Dict[str, str]:
    iot_client = get_iot_client()

    if event["RequestType"] in [
        CustomResourceTypes.RequestTypes.CREATE.value,
        CustomResourceTypes.RequestTypes.UPDATE.value,
    ]:
        iot_client.create_thing_group(
            thingGroupName=event["ResourceProperties"]["ThingGroupName"],
            tags=[{"Key": "cms-simulated-vehicle", "Value": "simulated-vehicle-group"}],
        )

    return {"THING_GROUP_NAME": event["ResourceProperties"]["ThingGroupName"]}


class CustomResourceTypes:
    class RequestTypes(Enum):
        CREATE = "Create"
        DELETE = "Delete"
        UPDATE = "Update"

    class ResourceTypes(Enum):
        CREATE_UUID = "CreateUUID"
        SEND_ANONYMOUS_METRICS = "SendAnonymousMetrics"
        CREATE_CONFIG = "CreateConfig"
        DETACH_IOT_POLICY = "DetachIoTPolicy"
        CREATE_USERPOOL_USER = "CreateUserpoolUser"
        COPY_TEMPLATE = "CopyTemplate"
        CREATE_IOT_THING_GROUP = "CreateIoTThingGroup"

    class StatusTypes(Enum):
        SUCCESS = "SUCCESS"
        FAILED = "FAILED"
