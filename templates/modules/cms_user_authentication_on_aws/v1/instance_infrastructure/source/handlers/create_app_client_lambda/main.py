# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Dict, List

# Third Party Libraries
import boto3
import botocore
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.config import Config

# Connected Mobility Solution on AWS
from .lib.status_type_enum import StatusType

if TYPE_CHECKING:
    # Third Party Libraries
    from mypy_boto3_cognito_idp.client import CognitoIdentityProviderClient
else:
    CognitoIdentityProviderClient = object

tracer = Tracer()
logger = Logger()


@lru_cache(maxsize=128)
def get_cognito_idp_client() -> CognitoIdentityProviderClient:
    return boto3.client(
        "cognito-idp", config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"])
    )


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    response: Dict[str, Any] = {
        "Status": StatusType.FAILED.value,
        "RequestId": context.aws_request_id,
    }

    cognito_identity_provider_client = get_cognito_idp_client()

    exception_messages = {
        cognito_identity_provider_client.exceptions.InvalidParameterException: "invalid parameter",
        cognito_identity_provider_client.exceptions.ResourceNotFoundException: "resource not found",
        cognito_identity_provider_client.exceptions.TooManyRequestsException: "too many requests",
        cognito_identity_provider_client.exceptions.LimitExceededException: "limit exceeded",
        cognito_identity_provider_client.exceptions.NotAuthorizedException: "unauthorized",
        cognito_identity_provider_client.exceptions.ScopeDoesNotExistException: "internal error",
        cognito_identity_provider_client.exceptions.InvalidOAuthFlowException: "invalid auth",
        cognito_identity_provider_client.exceptions.InternalErrorException: "internal error",
        cognito_identity_provider_client.exceptions.ConcurrentModificationException: "internal error",
        botocore.exceptions.ParamValidationError: "parameter validation failed",
    }

    try:
        response["Data"] = create_cognito_user_pool_app_client(
            client_name=event["CreateCognitoUserPoolAppClientInput"]["ClientName"],
            callback_urls=event["CreateCognitoUserPoolAppClientInput"]["CallbackURLs"],
            access_token_validity_minutes=event["CreateCognitoUserPoolAppClientInput"][
                "AccessTokenValidityMinutes"
            ],
            id_token_validity_minutes=event["CreateCognitoUserPoolAppClientInput"][
                "IdTokenValidityMinutes"
            ],
            refresh_token_validity_minutes=event["CreateCognitoUserPoolAppClientInput"][
                "RefreshTokenValidityMinutes"
            ],
        )
        response["Status"] = StatusType.SUCCESS.value
        logger.info("Successfully created app client: %s", response)
    except tuple(exception_messages.keys()) as exception:  # type: ignore
        response["Status"] = StatusType.FAILED.value
        response["ErrorMessage"] = exception_messages[type(exception)]
        logger.error(
            "Encountered error while creating App Client!",
            exc_info=True,
        )

    return response


@tracer.capture_method
def create_cognito_user_pool_app_client(
    client_name: str,
    callback_urls: List[str],
    access_token_validity_minutes: int,
    id_token_validity_minutes: int,
    refresh_token_validity_minutes: int,
) -> Dict[str, Any]:
    cognito_identity_provider_client = get_cognito_idp_client()

    response = cognito_identity_provider_client.create_user_pool_client(
        UserPoolId=os.environ["COGNITO_USER_POOL_ID"],
        ClientName=client_name,
        CallbackURLs=callback_urls,
        PreventUserExistenceErrors="ENABLED",
        AccessTokenValidity=access_token_validity_minutes,
        IdTokenValidity=id_token_validity_minutes,
        RefreshTokenValidity=refresh_token_validity_minutes,
        TokenValidityUnits={
            "AccessToken": "minutes",
        },
        GenerateSecret=True,
        AllowedOAuthFlows=["code"],
    )

    return {"ClientId": response["UserPoolClient"]["ClientId"]}
