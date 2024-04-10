# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json
import os
import time
from functools import _lru_cache_wrapper, lru_cache
from typing import Any, Dict, List

# Third Party Libraries
import jwt
import requests

# AWS Libraries
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

# CMS Common Library
from cms_common.auth.auth_configs import AuthConfigError, CMSIdPConfig, get_idp_config
from cms_common.cache.ttl_cache import get_ttl_cache_check

# Connected Mobility Solution on AWS
from .lib.custom_exceptions import (
    ExpirationError,
    IdPAudError,
    ScopeError,
    SigningKidError,
    TokenClaimsError,
    TokenDecodeError,
    WellKnownJWKError,
)

tracer = Tracer()
logger = Logger()

MAX_CACHE_SIZE_CONFIG = 1
MAX_CACHE_SIZE_TOKENS = 1024

# Usage:
#   This function is designed to work with any OAuth2.0 compliant IdP, and can validate both CMS user and service access tokens.
#   It requires a secret with IdP configurations necessary to complete the authorization code flow token exchange. This secret has
#   an expected JSON structure. See cms_common.auth_config for the JSON data structures.
#
# Caching:
#   For each unique token and idp_config combination, the entire verification will be cached. 1024 unique tokens can be cached.
#   A TTL of 10 minutes is applied to any cache which gets resources from the AWS account that might change without invalidating the cache.
@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    token_validation_response: Dict[str, Any] = {
        "validated": False,
        "status_code": None,
        "message": None,
    }

    # Validation steps
    # 1. Get IdP Config (cached)
    # 2. Not expired
    # 3. Verify Token (cached):
    #   - The signing token was from a known KID
    #   - Valid, non-malformed signature
    #   - Known iss and aud (if present)
    #   - At least 1 known scope
    try:
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
            token: str = event["Token"]
        except KeyError as e:
            logger.error(
                "KeyError while accessing Lambda event. Ensure event has the expected values.",
                exc_info=True,
            )
            raise e

        idp_config = get_cached_idp_config(
            user_agent_string=user_agent_string,
            identity_provider_id=identity_provider_id,
        )

        token_claims = get_cached_token_claims(token)  # Doesn't perform verification

        verify_expiration(
            token_claims
        )  # Verify expiration explicitly to allow for caching the other claim verifications via `verify_token`.

        verify_using_alternate_aud = token_claims.get("aud") is None
        if verify_using_alternate_aud and idp_config.alternate_aud_key is None:
            raise IdPAudError(
                "Token does not have aud key, and no alternate aud key is specified."
            )

        token_validation_response["validated"] = verify_and_cache_token(
            token=token,
            idp_config=idp_config,
            verify_using_alternate_aud=verify_using_alternate_aud,
        )
        token_validation_response["message"] = "Token validation successful!"
        token_validation_response["status_code"] = 200
        logger.info(token_validation_response["message"])
    except (
        AuthConfigError,
        WellKnownJWKError,
        TokenClaimsError,
        SigningKidError,
        ExpirationError,
        ScopeError,
        IdPAudError,
    ) as e:
        logger.error(
            e.message,
            exc_info=True,
        )
        token_validation_response[
            "message"
        ] = "Could not validate token. See status code."
        token_validation_response["status_code"] = e.code
        clear_caches()
    except KeyError as e:
        token_validation_response[
            "message"
        ] = "Could not validate token. See status code."
        token_validation_response["status_code"] = 500
        clear_caches()

    return token_validation_response


def clear_caches() -> None:
    cached_functions: List[_lru_cache_wrapper[Any]] = [
        get_cached_idp_config,
        get_cached_token_claims,
        get_cached_issuer_jwks,
        verify_and_cache_token,
    ]
    for function in cached_functions:
        function.cache_clear()


# ========= GETTERS =========
@lru_cache(maxsize=MAX_CACHE_SIZE_CONFIG)
@tracer.capture_method
def get_cached_idp_config(
    user_agent_string: str,
    identity_provider_id: str,
    ttl_cache_check: int = get_ttl_cache_check(),  # Add a TTL to cache in case of SSM or Secrets Manager value changes.
) -> CMSIdPConfig:
    return get_idp_config(
        user_agent_string=user_agent_string,
        identity_provider_id=identity_provider_id,
    )


@lru_cache(maxsize=MAX_CACHE_SIZE_TOKENS)
@tracer.capture_method
def get_cached_token_claims(token: str) -> Dict[str, Any]:
    try:
        claims: Dict[str, Any] = jwt.decode(token, options={"verify_signature": False})
        return claims
    except jwt.exceptions.DecodeError as e:
        raise TokenDecodeError("Validation Failure: token could not be decoded.") from e


@tracer.capture_method
def verify_expiration(
    token_claims: Dict[str, Any],
) -> None:
    try:
        if time.time() > token_claims["exp"]:
            raise ExpirationError("Validation Failure: token is expired.")
    except KeyError as e:
        raise ExpirationError("Validation Failure: token is missing exp key.") from e


@lru_cache(maxsize=MAX_CACHE_SIZE_TOKENS)
@tracer.capture_method
def verify_and_cache_token(
    token: str, idp_config: CMSIdPConfig, verify_using_alternate_aud: bool
) -> bool:
    well_known_jwks = get_cached_issuer_jwks(idp_config.iss_domain)
    token_jwk = verify_signing_kid(token, well_known_jwks)
    issuer = f"https://{idp_config.iss_domain}"

    if not verify_using_alternate_aud:
        token_claims = verify_claims(
            token,
            token_jwk,
            issuer=issuer,
            audience=idp_config.auds,
        )  # Validate iss and aud during decode
    else:
        token_claims = verify_claims(
            token, token_jwk, issuer, audience=None
        )  # Set audience to None to 'skip' aud check during decode
        verify_alternate_aud(
            alternate_aud_key=str(idp_config.alternate_aud_key),
            known_auds=idp_config.auds,
            token_claims=token_claims,
        )
    verify_scope(token_claims, idp_config.scopes)

    return True


@lru_cache(maxsize=MAX_CACHE_SIZE_CONFIG)
@tracer.capture_method
def get_cached_issuer_jwks(iss_domain: str) -> List[Dict[str, str]]:
    try:
        known_jwks: List[Dict[str, str]] = requests.get(
            f"https://{iss_domain.rstrip('/')}/.well-known/jwks.json",
            timeout=10,
        ).json()["keys"]
    except KeyError as e:
        raise WellKnownJWKError(
            "Validation Failure: the retrieved JWKs did not have the expected 'keys' key. This is likely an issue with the response provided by your IdP."
        ) from e
    except requests.RequestException as e:
        raise WellKnownJWKError(
            "Validation Failure: request exception while attempting to retrieve the known JWKs."
        ) from e
    except json.JSONDecodeError as e:
        raise WellKnownJWKError(
            "Validation Failure: well known JWKs response could not be decoded as JSON."
        ) from e
    return known_jwks


@tracer.capture_method
def verify_signing_kid(
    token: str, well_known_jwks: List[Dict[str, str]]
) -> Dict[str, str]:
    # Verifies that the KID used to sign the token matches a KID from our list of
    # well known JWKs associated with our IdP's "user pool".
    try:
        token_kid = jwt.get_unverified_header(token)["kid"]
    except jwt.exceptions.DecodeError as e:
        raise SigningKidError(
            "Validation Failure: token header could not be decoded."
        ) from e
    except KeyError as e:
        raise SigningKidError(
            "Validation Failure: token header does not contain `kid` key."
        ) from e
    token_jwk = None
    try:
        for user_pool_jwk in well_known_jwks:
            if user_pool_jwk["kid"] == token_kid:
                token_jwk = user_pool_jwk
                break
    except KeyError as e:
        raise SigningKidError(
            "Validation Failure: returned well known JWKs do not all have a `kid` key."
        ) from e
    if token_jwk is None:
        raise SigningKidError(
            "Validation Failure: key id for the token did not match a public key id for the issuer."
        )
    return token_jwk


@tracer.capture_method
def verify_claims(
    token: str, token_jwk: Dict[str, str], issuer: str, audience: List[str] | None
) -> Dict[str, Any]:
    try:
        token_public_key = jwt.get_algorithm_by_name("RS256").from_jwk(
            json.dumps(token_jwk)
        )
        token_claims: Dict[str, Any] = jwt.decode(
            token,
            key=token_public_key,
            algorithms=["RS256"],
            issuer=issuer,
            audience=audience,
        )
    except jwt.exceptions.MissingRequiredClaimError as e:
        raise TokenClaimsError(
            "Validation Failure: token missing required claims."
        ) from e
    except jwt.exceptions.InvalidSignatureError as e:
        raise TokenClaimsError(
            "Validation Failure: signature verification failed."
        ) from e
    except jwt.exceptions.InvalidKeyError as e:
        raise TokenClaimsError(
            "Validation Failure: could not construct public key from token JWK."
        ) from e
    except jwt.exceptions.InvalidAudienceError as e:
        raise TokenClaimsError("Validation Failure: token audience is invalid.") from e
    except jwt.exceptions.InvalidIssuerError as e:
        raise TokenClaimsError("Validation Failure: token issuer is invalid.") from e
    except jwt.exceptions.DecodeError as e:
        raise TokenClaimsError("Validation Failure: token failed to decode.") from e
    return token_claims


@tracer.capture_method
def verify_alternate_aud(
    alternate_aud_key: str,
    known_auds: List[str],
    token_claims: Dict[str, Any],
) -> None:
    try:
        if token_claims[alternate_aud_key] not in known_auds:
            raise IdPAudError(
                f"Validation Failure: {alternate_aud_key} was not a known client."
            )
    except KeyError as e:
        raise IdPAudError(
            "Validation Failure: token did not have the expected alternate aud key."
        ) from e


@tracer.capture_method
def verify_scope(
    token_claims: Dict[str, Any],
    known_scopes: List[str],
) -> None:
    # At least one scope must be match a known scope from the list of known scopes configured with the IdP.
    # The scopes are associated with clients, and there can be any numbers of clients with any number of scopes.
    try:
        token_scopes: List[str] = token_claims["scope"].split(
            " "
        )  # Scopes are always a space separated list
        if len(set(known_scopes).intersection(token_scopes)) == 0:
            raise ScopeError("Validation Failure: token did not have a known scope.")
    except KeyError as e:
        raise ScopeError("Validation Failure: token did not have a scope claim.") from e
