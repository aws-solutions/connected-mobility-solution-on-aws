# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json
import os
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Dict

# Third Party Libraries
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

AUTHORIZATION_HEADER_PREFIX = "Bearer"


@lru_cache(maxsize=128)
def get_lambda_client() -> LambdaClient:
    return boto3.client(
        "lambda", config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"])
    )


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    response = {
        "isAuthorized": False,
    }

    try:
        token = get_token(event["authorizationToken"])
        token_use = os.environ["TOKEN_USE"]

        # Call token validation lambda
        token_validation_response = get_lambda_client().invoke(
            FunctionName=os.environ["TOKEN_VALIDATION_LAMBDA_ARN"],
            InvocationType="RequestResponse",
            Payload=json.dumps(
                {
                    "TokenValidationProperties": {
                        "Token": token,
                        "TokenUse": token_use,
                    }
                }
            ),
        )

        token_validation_response_payload = json.loads(
            token_validation_response["Payload"].read().decode("utf-8")
        )

        response["isAuthorized"] = token_validation_response_payload["isTokenValid"]
        logger.info(token_validation_response_payload["message"])

    except (ValueError, ClientError, KeyError):
        logger.error("Error validating token", exc_info=True)

    return response


def get_token(auth_header: str) -> str:
    bearer, token = auth_header.split(" ", maxsplit=2)
    if bearer != AUTHORIZATION_HEADER_PREFIX:
        raise ValueError("Invalid token")

    return token
