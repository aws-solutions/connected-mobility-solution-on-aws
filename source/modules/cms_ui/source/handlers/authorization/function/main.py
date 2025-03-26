# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json
import os
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Dict

# AWS Libraries
import boto3
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.config import Config
from botocore.exceptions import ClientError

if TYPE_CHECKING:
    # Third Party Libraries
    from mypy_boto3_lambda import LambdaClient
else:
    LambdaClient = object

tracer = Tracer()
logger = Logger()


@lru_cache(maxsize=1)
def get_lambda_client() -> LambdaClient:
    return boto3.client(
        "lambda", config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"])
    )


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    is_authorized = False

    try:
        token = event["headers"]["Authorization"]

        # Call token validation lambda
        token_validation_response = get_lambda_client().invoke(
            FunctionName=os.environ["TOKEN_VALIDATION_LAMBDA_ARN"],
            InvocationType="RequestResponse",
            Payload=json.dumps(
                {"Token": token, "SpecifiedAud": os.environ["AUTHORIZATION_AUD"]}
            ),
        )

        token_validation_response_payload = json.loads(
            token_validation_response["Payload"].read().decode("utf-8")
        )

        is_authorized = token_validation_response_payload["validated"]
        logger.info(token_validation_response_payload["message"])

    except (ValueError, ClientError, KeyError):
        logger.error("Error validating token", exc_info=True)

    return {
        "principalId": "*",
        "policyDocument": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "*",
                    "Effect": "Allow" if is_authorized is True else "Deny",
                    "Resource": "*",
                }
            ],
        },
    }
