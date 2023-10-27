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
import requests
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.parameters import get_secret
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.config import Config
from botocore.exceptions import ClientError

# Connected Mobility Solution on AWS
from .lib.custom_exceptions import TokenExchangeError, TokenValidationError

if TYPE_CHECKING:
    # Third Party Libraries
    from mypy_boto3_lambda import LambdaClient
else:
    LambdaClient = object


tracer = Tracer()
logger = Logger()


@lru_cache(maxsize=128)
def get_lambda_client() -> LambdaClient:
    return boto3.client(
        "lambda", config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"])
    )


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    user_authentication_response: Dict[str, Any] = {
        "isAuthenticated": False,
    }
    try:
        client_id = os.environ["USER_CLIENT_ID"]
        client_secret = get_secret(
            name=os.environ["USER_CLIENT_SECRET_ARN"], max_age=300
        )
        redirect_uri = os.environ["REDIRECT_URI"]
        domain_prefix = os.environ["DOMAIN_PREFIX"]
        user_pool_region = os.environ["USER_POOL_REGION"]
        code = event["TokenExchangeProperties"]["AuthorizationCode"]
        code_verifier = event["TokenExchangeProperties"]["CodeVerifier"]

        # Exchange authorization code for user tokens
        user_tokens_response: Dict[str, Any] = get_user_tokens(
            client_id=client_id,
            client_secret=str(client_secret),
            redirect_uri=redirect_uri,
            code=code,
            code_verifier=code_verifier,
            domain_prefix=domain_prefix,
            user_pool_region=user_pool_region,
        )
        id_token = user_tokens_response["id_token"]
        access_token = user_tokens_response["access_token"]

        # Validate the integrity of the user tokens: https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html
        validate_token(  # nosec
            token=id_token,
            token_use="id",
            client_id=client_id,
        )
        validate_token(  # nosec
            token=access_token,
            token_use="access",
            client_id=client_id,
        )

        user_authentication_response["user_tokens"] = user_tokens_response
        user_authentication_response["isAuthenticated"] = True
        logger.info("User has been authenticated. Returning user tokens.")

    except KeyError:
        logger.error(
            "The lambda event did not contain the necessary parameters or environment setup.",
            exc_info=True,
        )
    except (
        TokenExchangeError,
        TokenValidationError,
    ):
        logger.error(
            "Error while exchanging tokens.",
            exc_info=True,
        )

    return user_authentication_response


@tracer.capture_method
def get_user_tokens(
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    code: str,
    code_verifier: str,
    domain_prefix: str,
    user_pool_region: str,
) -> Dict[str, Any]:

    request_body = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "code": code,
        # The code_verifier is used by Cognito to ensure the authorization_code has not been compromised before returning tokens.
        "code_verifier": code_verifier,
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    }

    try:
        user_tokens_response = requests.post(
            f"https://{domain_prefix}.auth.{user_pool_region}.amazoncognito.com/oauth2/token",
            data=request_body,
            headers=headers,
            timeout=10,
        )
        user_tokens_response.raise_for_status()
    except requests.exceptions.RequestException as exception:
        raise TokenExchangeError(
            "Could not successfully retrieve user tokens."
        ) from exception

    logger.info("User tokens successfully retrieved.")
    json_response: Dict[str, Any] = user_tokens_response.json()
    return json_response


def validate_token(
    token: str,
    token_use: str,
    client_id: str,
) -> None:
    try:
        # Call token validation lambda
        token_validation_response = get_lambda_client().invoke(
            FunctionName=os.environ["TOKEN_VALIDATION_LAMBDA_ARN"],
            InvocationType="RequestResponse",
            Payload=json.dumps(
                {
                    "TokenValidationProperties": {
                        "ClientId": client_id,
                        "Token": token,
                        "TokenUse": token_use,
                    }
                }
            ).encode(),
        )

        token_validation_response_payload = json.loads(
            token_validation_response["Payload"].read().decode("utf-8")
        )

        if token_validation_response_payload["isTokenValid"] is False:
            raise TokenValidationError(
                f"Token validation failed: {token_validation_response_payload['message']}"
            )

    except (ValueError, ClientError, KeyError) as exception:
        raise TokenValidationError(
            f"Token validation failed: {str(exception)}"
        ) from exception
