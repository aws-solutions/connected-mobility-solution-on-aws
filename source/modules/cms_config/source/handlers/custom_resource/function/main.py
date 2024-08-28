# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json
import uuid
from typing import Any, Dict

# Third Party Libraries
import requests

# AWS Libraries
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

# CMS Common Library
from cms_common.enums.custom_resource import (
    CustomResourceRequestType,
    CustomResourceStatusType,
)

# Connected Mobility Solution on AWS
from .lib.custom_resource_type_enum import CustomResourceFunctionType

tracer = Tracer()
logger = Logger()


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    response = {"Status": CustomResourceStatusType.SUCCESS.value, "Data": {}}
    reason = f"See the details in CloudWatch Log Stream: {context.log_stream_name}"

    try:

        match event["ResourceProperties"]["Resource"]:
            case CustomResourceFunctionType.CREATE_DEPLOYMENT_UUID.value:
                response["Data"] = create_deployment_uuid(event)
            case _:
                raise KeyError(
                    f"No Custom Resource Type: {event['ResourceProperties']['Resource']}"
                )

    except Exception as exception:  # pylint: disable=broad-exception-caught
        # Wrap all exceptions so CloudFormation doesn't hang
        logger.error("CustomResource error: %s", str(exception), exc_info=True)
        response["Status"] = CustomResourceStatusType.FAILED.value
        reason = f"{str(exception)} ... {reason}"

    send_cloud_formation_response(
        event,
        response,
        reason,
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


@tracer.capture_method
def create_deployment_uuid(event: Dict[str, Any]) -> Dict[str, Any]:
    response = {}

    if event["RequestType"] == CustomResourceRequestType.CREATE.value:
        response["SolutionUUID"] = str(uuid.uuid4())

    return response
