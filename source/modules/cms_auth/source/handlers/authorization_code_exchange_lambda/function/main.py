# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
from functools import lru_cache
from typing import Any, Dict

# Third Party Libraries
import requests

# AWS Libraries
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

# CMS Common Library
from cms_common.auth.auth_configs import (
    AuthConfigError,
    CMSClientConfig,
    CMSIdPConfig,
    get_idp_config,
    get_user_client_config,
)
from cms_common.cache.ttl_cache import get_ttl_cache_check

# Connected Mobility Solution on AWS
from .lib.custom_exceptions import AuthorizationCodeExchangeError

tracer = Tracer()
logger = Logger()

MAX_CACHE_SIZE_CONFIG = 1

# Usage:
#   This function exchanged an authorization code for an access token via a user specified /token endpoint, as defined in OAuth standards. It requires
#   a secret with IdP configurations necessary to complete the authorization code flow token exchange. This secret has an expected JSON structure.
#   See cms_common.auth_config for the JSON data structures.
#
# Caching:
#   The IdP config retrieved from Secrets Manager is cached with a max cache size of only 1. A TTL of 10 minutes is
#   applied to this cache in case the IdP config secret or SSM parameter value changes without invalidating the cache.
@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    authorization_code_exchange_response: Dict[str, Any] = {
        "authenticated": False,
        "user_tokens": None,
        "status_code": None,
        "message": None,
    }

    try:  # Authenticate authorization code and exchange for user tokens
        try:
            identity_provider_id = os.environ["IDENTITY_PROVIDER_ID"]
            user_agent_string = os.environ["USER_AGENT_STRING"]
        except KeyError as e:
            logger.error(
                "KeyError while accessing Lambda environment. Ensure environment has the expected values.",
                exc_info=True,
            )
            raise e

        try:
            code = event["AuthorizationCode"]
            redirect_uri = event["RedirectUri"]
            code_verifier = event.get(
                "CodeVerifier", ""
            )  # CodeVerifier is optional depending on if Authorization Code Grant used PKCE
        except KeyError as e:
            logger.error(
                "KeyError while accessing Lambda event. Ensure event has the expected values.",
                exc_info=True,
            )
            raise e

        client_config = get_cached_user_client_config(
            user_agent_string=user_agent_string,
            identity_provider_id=identity_provider_id,
        )

        idp_config = get_cached_idp_config(
            user_agent_string=user_agent_string,
            identity_provider_id=identity_provider_id,
        )

        authorization_code_exchange_response["user_tokens"] = get_user_tokens(
            token_endpoint=idp_config.token_endpoint,
            client_id=client_config.client_id,
            client_secret=client_config.client_secret,
            redirect_uri=redirect_uri,
            code=code,
            code_verifier=code_verifier,
        )

        authorization_code_exchange_response["authenticated"] = True
        authorization_code_exchange_response[
            "message"
        ] = "User has been authenticated. Returning user tokens."
        authorization_code_exchange_response["status_code"] = 200
        logger.info(authorization_code_exchange_response["message"])
    except (AuthorizationCodeExchangeError, AuthConfigError) as e:
        logger.error(
            e.message,
            exc_info=True,
        )
        authorization_code_exchange_response[
            "message"
        ] = "Could not exchange token. See status code."
        authorization_code_exchange_response["status_code"] = e.code
    except KeyError as e:
        authorization_code_exchange_response[
            "message"
        ] = "Could not exchange token. See status code."
        authorization_code_exchange_response["status_code"] = 500

    return authorization_code_exchange_response


# ========= GETTERS =========
@lru_cache(maxsize=MAX_CACHE_SIZE_CONFIG)
@tracer.capture_method
def get_cached_user_client_config(
    user_agent_string: str,
    identity_provider_id: str,
    ttl_cache_check: int = get_ttl_cache_check(),
) -> CMSClientConfig:
    return get_user_client_config(
        user_agent_string=user_agent_string,
        identity_provider_id=identity_provider_id,
    )


@lru_cache(maxsize=MAX_CACHE_SIZE_CONFIG)
@tracer.capture_method
def get_cached_idp_config(
    user_agent_string: str,
    identity_provider_id: str,
    ttl_cache_check: int = get_ttl_cache_check(),
) -> CMSIdPConfig:
    return get_idp_config(
        user_agent_string=user_agent_string,
        identity_provider_id=identity_provider_id,
    )


@tracer.capture_method
def get_user_tokens(
    token_endpoint: str,
    client_id: str,
    client_secret: str,
    redirect_uri: str,
    code: str,
    code_verifier: str,
) -> Dict[str, Any]:
    request_body = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "code": code,
        "code_verifier": code_verifier,
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    }

    try:
        user_tokens_response = requests.post(
            token_endpoint,
            data=request_body,
            headers=headers,
            timeout=10,
        )
        user_tokens_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise AuthorizationCodeExchangeError(
            "Authorization Code Exchange Error: could not successfully retrieve user tokens."
        ) from e

    logger.info("User tokens successfully retrieved.")
    json_response: Dict[str, Any] = user_tokens_response.json()
    return json_response
