# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
import time
from functools import lru_cache
from typing import Any, Dict

# Third Party Libraries
import requests
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from jose import JWTError, jwk, jwt
from jose.utils import base64url_decode

# Connected Mobility Solution on AWS
from .lib.custom_exceptions import (
    TokenExpirationError,
    TokenValidationError,
    UserClaimsError,
)

tracer = Tracer()
logger = Logger()


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    token_validation_response: Dict[str, Any] = {
        "isTokenValid": False,
        "message": None,
    }

    try:
        associated_client_id = ""
        user_pool_region = os.environ["USER_POOL_REGION"]
        user_pool_id = os.environ["USER_POOL_ID"]
        user_client_id = os.environ["USER_CLIENT_ID"]
        service_client_id = os.environ["SERVICE_CLIENT_ID"]
        formatted_cms_service_scope = os.environ["FORMATTED_CMS_SERVICE_SCOPE"]
        token = event["TokenValidationProperties"]["Token"]
        token_use = event["TokenValidationProperties"]["TokenUse"]

        # Validate the integrity of the user tokens: https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html
        check_token_validity(token)

        token_claims = jwt.get_unverified_claims(token)

        # If an access token came from a CMS service, it will contain the expected scope, and we will check claims against the service_client_id
        # Otherwise, the access token can be assumed to be from a user, in which case we use the user client id
        if (
            "scope" in token_claims.keys()
            and token_claims["scope"] == formatted_cms_service_scope
        ):
            associated_client_id = service_client_id
        else:
            associated_client_id = user_client_id

        # Verify expiration
        check_token_expiration(token_claims)

        # Validate user claims
        check_user_claims(
            user_pool_region=user_pool_region,
            user_pool_id=user_pool_id,
            client_id=associated_client_id,
            token_claims=token_claims,
            token_use=token_use,
        )

        token_validation_response["isTokenValid"] = True
        token_validation_response["message"] = "Token validation successful!"
    except KeyError:
        logger.error(
            "The lambda event did not contain the necessary parameters or environment setup.",
            exc_info=True,
        )
        token_validation_response[
            "message"
        ] = "Error: event body is missing required values."
    except TokenExpirationError:
        logger.error(
            f"Token is expired, ClientID: {associated_client_id}, UserPoolID: {user_pool_id}",
            exc_info=True,
        )
        token_validation_response["message"] = "Error: token is expired."
    except TokenValidationError:
        logger.error(
            f"Token is invalid, ClientID: {associated_client_id}, UserPoolID: {user_pool_id}",
            exc_info=True,
        )
        token_validation_response["message"] = "Error: token is invalid."
    except UserClaimsError:
        logger.error(
            f"User claims are invalid, ClientID: {associated_client_id}, UserPoolID: {user_pool_id}",
            exc_info=True,
        )
        token_validation_response["message"] = "Error: user claims are invalid."
    except JWTError:
        logger.error(
            "Could not decode token.",
            exc_info=True,
        )
        token_validation_response["message"] = "Error: could not decode token."

    return token_validation_response


@lru_cache(maxsize=128)
def get_user_pool_jwks() -> Any:
    return requests.get(
        f"https://cognito-idp.{os.environ['USER_POOL_REGION']}.amazonaws.com/{os.environ['USER_POOL_ID']}/.well-known/jwks.json",
        timeout=10,
    ).json()["keys"]


# JWT Validation done via python-jose library: https://pypi.org/project/python-jose/
def check_token_validity(token: str) -> None:
    # Validate Key ID
    token_kid = jwt.get_unverified_header(token)["kid"]
    token_jwk = None
    for user_pool_jwk in get_user_pool_jwks():
        if user_pool_jwk["kid"] == token_kid:
            token_jwk = user_pool_jwk
            break
    if token_jwk is None:
        raise TokenValidationError(
            "Validation Failure, key id for the id token did not match the public key id for the user pool."
        )

    # Validate token signature
    token_public_key = jwk.construct(key_data=token_jwk, algorithm="RS256")
    message, encoded_signature = token.rsplit(".", 1)
    decoded_signature = base64url_decode(encoded_signature.encode("utf-8"))

    if not token_public_key.verify(message.encode("utf-8"), decoded_signature):
        raise TokenValidationError("Validation Failure, signature verification failed.")


def check_token_expiration(token_claims: Dict[str, Any]) -> None:
    try:
        if time.time() > token_claims["exp"]:
            raise TokenExpirationError("Validation Failure, token is expired.")
    except KeyError as exception:
        raise TokenExpirationError(
            "Validation Failure, token did not have an expiration claim."
        ) from exception


# Validate the token's user info via steps defined here: https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html
def check_user_claims(
    user_pool_region: str,
    user_pool_id: str,
    client_id: str,
    token_claims: Dict[str, Any],
    token_use: str,
) -> None:
    try:
        user_claim_checks = [
            (
                token_claims["aud" if token_use == "id" else "client_id"]  # nosec
                != client_id,
                "Validation Failure, user claims did not match the client id.",
            ),
            (
                token_claims["iss"]
                != f"https://cognito-idp.{user_pool_region}.amazonaws.com/{user_pool_id}",
                "Validation Failure, id token issuer did not match the user pool.",
            ),
            (
                token_claims["token_use"] != token_use,
                "Validation Failure, user tokens do not have the correct usage.",
            ),
        ]

        for user_claim_check, error_message in user_claim_checks:
            if user_claim_check:
                raise UserClaimsError(error_message)

    except KeyError as exception:
        raise UserClaimsError(
            "Validation failure, the user tokens did not have all the expected claims."
        ) from exception
