# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json
import os
import uuid
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Dict

# Third Party Libraries
import boto3
import requests
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.config import Config

# Connected Mobility Solution on AWS
from .lib.custom_resource_type_enum import CustomResourceType

if TYPE_CHECKING:
    # Third Party Libraries
    from mypy_boto3_cognito_idp.client import CognitoIdentityProviderClient
else:
    CognitoIdentityProviderClient = object

tracer = Tracer()
logger = Logger()


@lru_cache(maxsize=128)
def get_cognito_client() -> CognitoIdentityProviderClient:
    return boto3.client(
        "cognito-idp", config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"])
    )


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    response = {"Status": CustomResourceType.StatusType.FAILED.value, "Data": {}}

    resource_map = {
        CustomResourceType.ResourceType.MANAGE_USER_POOL_DOMAIN.value: manage_user_pool_domain,
    }

    try:
        response["Data"] = resource_map[event["ResourceProperties"]["Resource"]](event)
        response["Status"] = CustomResourceType.StatusType.SUCCESS.value
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


@tracer.capture_method
def manage_user_pool_domain(event: Dict[str, Any]) -> Dict[str, Any]:
    user_pool_domain_response: Dict[str, Any] = {"user_pool_domain": None}

    if event["RequestType"] == CustomResourceType.RequestType.CREATE.value:
        user_pool_id = event["ResourceProperties"]["UserPoolId"]

        short_uid = uuid.uuid4().hex[:8]
        user_pool_domain_prefix = f"cms-login-{short_uid}"

        get_cognito_client().create_user_pool_domain(
            Domain=user_pool_domain_prefix,
            UserPoolId=user_pool_id,
        )
        logger.info(
            f"Successfully created user pool domain with prefix: {user_pool_domain_prefix}"
        )
        user_pool_domain_response["domain_prefix"] = user_pool_domain_prefix

    elif event["RequestType"] == CustomResourceType.RequestType.DELETE.value:
        user_pool_id = event["ResourceProperties"]["UserPoolId"]
        user_pool = get_cognito_client().describe_user_pool(UserPoolId=user_pool_id)

        get_cognito_client().delete_user_pool_domain(
            Domain=user_pool["UserPool"]["Domain"],
            UserPoolId=user_pool_id,
        )
        logger.info(
            f"Successfully deleted user pool domain: {user_pool['UserPool']['Domain']}"
        )

    return user_pool_domain_response
