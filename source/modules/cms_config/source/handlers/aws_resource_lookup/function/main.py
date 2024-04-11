# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json
import os
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Dict

# Third Party Libraries
import requests

# AWS Libraries
import boto3
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.config import Config

# CMS Common Library
from cms_common.enums.aws_resource_lookup import AwsResourceLookupCustomResourceType
from cms_common.enums.custom_resource import (
    CustomResourceRequestType,
    CustomResourceStatusType,
)

if TYPE_CHECKING:
    # Third Party Libraries
    from mypy_boto3_ssm import SSMClient
else:
    SSMClient = object


tracer = Tracer()
logger = Logger()


MAX_CACHE_SIZE_CLIENTS = 1


@lru_cache(maxsize=MAX_CACHE_SIZE_CLIENTS)
def get_ssm_client() -> SSMClient:
    return boto3.client(
        "ssm", config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"])
    )


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    response = {
        "Status": CustomResourceStatusType.FAILED.value,
        "Data": {},
    }

    resource_map = {
        AwsResourceLookupCustomResourceType.SSM_PARAMETERS.value: ssm_get_parameter
    }

    try:
        response["Data"] = resource_map[event["ResourceProperties"]["Resource"]](event)
        response["Status"] = CustomResourceStatusType.SUCCESS.value
    except Exception as exception:  # pylint: disable=W0703
        # Wrap all exceptions so CloudFormation doesn't hang
        logger.error("CustomResource error: %s", exception, exc_info=True)

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

    headers = {"Content-Type": "application/json"}

    requests.put(
        event["ResponseURL"],
        data=json.dumps(response_body),
        headers=headers,
        timeout=60,
    )


# BOTO "WRAPPERS"
@tracer.capture_method
def ssm_get_parameter(event: Dict[str, Any]) -> Dict[str, Any]:
    response = None
    if event["RequestType"] in [
        CustomResourceRequestType.CREATE.value,
        CustomResourceRequestType.UPDATE.value,
    ]:
        parameter_name = event["ResourceProperties"]["ParameterName"]
        response = get_ssm_client().get_parameter(Name=parameter_name)

        return {"parameter_value": response["Parameter"]["Value"]}

    return {}
