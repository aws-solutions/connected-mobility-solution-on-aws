# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any, Dict, List

# Third Party Libraries
import pytest

# Connected Mobility Solution on AWS
from ....handlers.token_validation_lambda.function.lib.custom_exceptions import (
    ExpirationError,
    IdPAudError,
    ScopeError,
    SigningKidError,
    TokenClaimsError,
    TokenDecodeError,
    WellKnownJWKError,
)
from ....handlers.token_validation_lambda.function.main import (
    get_cached_issuer_jwks,
    get_cached_token_claims,
    handler,
    verify_alternate_aud,
    verify_claims,
    verify_expiration,
    verify_scope,
    verify_signing_kid,
)
from ..fixtures.fixture_shared_jwt_mocks import (
    TEST_ALTERNATE_AUD_KEY,
    TEST_ISS_DOMAIN,
    TEST_KNOWN_AUDS,
)


# =============== HANDLER SUCCESS ===============
def test_handler_success_access_token(
    mock_token_validation_idp_config_valid: None,
    mock_well_known_jwks_valid: None,
    mock_token_validation_environment_valid: None,
    token_validation_event_valid_access_token: Dict[str, Any],
    context: Dict[str, Any],
) -> None:
    response = handler(
        token_validation_event_valid_access_token,
        context,
    )
    assert response["validated"] is True
    assert response["message"] == "Token validation successful!"


def test_handler_success_service_token(
    mock_token_validation_idp_config_valid: None,
    mock_token_validation_environment_valid: None,
    mock_well_known_jwks_valid: None,
    token_validation_event_valid_service_token: Dict[str, Any],
    context: Dict[str, Any],
) -> None:
    response = handler(
        token_validation_event_valid_service_token,
        context,
    )
    assert response["validated"] is True
    assert response["message"] == "Token validation successful!"


# =============== HANDLER FAILURE ===============
def test_handler_invalid_evironment(
    token_validation_event_valid_access_token: Dict[str, Any],
    context: Dict[str, Any],
) -> None:
    response = handler(
        token_validation_event_valid_access_token,
        context,
    )
    assert response["validated"] is False
    assert response["message"] == "Could not validate token. See status code."
    assert response["status_code"] == 500


def test_handler_invalid_event(
    mock_token_validation_environment_valid: None,
    context: Dict[str, Any],
) -> None:
    response = handler(
        {"Invalid Event Key": "Invalid Event Value"},
        context,
    )
    assert response["validated"] is False
    assert response["message"] == "Could not validate token. See status code."
    assert response["status_code"] == 500


def test_handler_signing_kid_error(
    mock_token_validation_idp_config_valid: None,
    mock_token_validation_environment_valid: None,
    mock_well_known_jwks_unknown_jwks: None,
    token_validation_event_valid_access_token: Dict[str, Any],
    context: Dict[str, Any],
) -> None:
    response = handler(
        token_validation_event_valid_access_token,
        context,
    )
    assert response["validated"] is False
    assert response["message"] == "Could not validate token. See status code."
    assert response["status_code"] == 401


def test_handler_signature_verification_error(
    mock_token_validation_idp_config_valid: None,
    mock_token_validation_environment_valid: None,
    mock_well_known_jwks_valid: None,
    token_validation_event_incorrect_kid_token: Dict[str, Any],
    context: Dict[str, Any],
) -> None:
    response = handler(
        token_validation_event_incorrect_kid_token,
        context,
    )
    assert response["validated"] is False
    assert response["message"] == "Could not validate token. See status code."
    assert response["status_code"] == 401


def test_handler_invalid_idp_config_error(
    mock_token_validation_environment_valid: None,
    token_validation_event_valid_access_token: Dict[str, Any],
    context: Dict[str, Any],
) -> None:
    response = handler(
        token_validation_event_valid_access_token,
        context,
    )
    assert response["validated"] is False
    assert response["message"] == "Could not validate token. See status code."
    assert response["status_code"] == 500


def test_handler_well_known_jwk_error(
    mock_token_validation_idp_config_valid: None,
    mock_token_validation_environment_valid: None,
    mock_well_known_jwks_invalid_key_error: None,
    token_validation_event_valid_access_token: Dict[str, Any],
    context: Dict[str, Any],
) -> None:
    response = handler(
        token_validation_event_valid_access_token,
        context,
    )
    assert response["validated"] is False
    assert response["message"] == "Could not validate token. See status code."
    assert response["status_code"] == 500


def test_handler_idp_claims_error(
    mock_token_validation_idp_config_valid: None,
    mock_token_validation_environment_valid: None,
    mock_well_known_jwks_valid: None,
    token_validation_event_invalid_token_claims: Dict[str, Any],
    context: Dict[str, Any],
) -> None:
    response = handler(
        token_validation_event_invalid_token_claims,
        context,
    )
    assert response["validated"] is False
    assert response["message"] == "Could not validate token. See status code."
    assert response["status_code"] == 401


def test_handler_expiration_error(
    mock_token_validation_idp_config_valid: None,
    mock_token_validation_environment_valid: None,
    token_validation_event_expired_token: Dict[str, Any],
    context: Dict[str, Any],
) -> None:
    response = handler(
        token_validation_event_expired_token,
        context,
    )
    assert response["validated"] is False
    assert response["message"] == "Could not validate token. See status code."
    assert response["status_code"] == 401


def test_handler_scope_error(
    mock_token_validation_idp_config_valid: None,
    mock_token_validation_environment_valid: None,
    mock_well_known_jwks_valid: None,
    token_validation_event_invalid_scope_service_token: Dict[str, Any],
    context: Dict[str, Any],
) -> None:
    response = handler(
        token_validation_event_invalid_scope_service_token,
        context,
    )
    assert response["validated"] is False
    assert response["message"] == "Could not validate token. See status code."
    assert response["status_code"] == 401


# =============== GET_CACHED_ISSUER_JWKS ===============
def test_get_cached_issuer_jwks_key_error(
    mock_well_known_jwks_invalid_key_error: None,
) -> None:
    with pytest.raises(
        WellKnownJWKError,
        match=r"Validation Failure: the retrieved JWKs did not have the expected 'keys' key. This is likely an issue with the response provided by your IdP.",
    ):
        get_cached_issuer_jwks(TEST_ISS_DOMAIN)


def test_get_cached_issuer_jwks_client_error() -> None:
    with pytest.raises(
        WellKnownJWKError,
        match=r"Validation Failure: request exception while attempting to retrieve the known JWKs.",
    ):
        get_cached_issuer_jwks(TEST_ISS_DOMAIN)


def test_get_cached_issuer_jwks_decode_error(
    mock_well_known_jwks_decode_error: None,
) -> None:
    with pytest.raises(
        WellKnownJWKError,
        match=r"Validation Failure: well known JWKs response could not be decoded as JSON.",
    ):
        get_cached_issuer_jwks(TEST_ISS_DOMAIN)


# =============== GET_CACHED_TOKEN_CLAIMS ===============
def test_get_cached_token_claims_decode_error() -> None:
    with pytest.raises(
        TokenDecodeError, match=r"Validation Failure: token could not be decoded."
    ):
        get_cached_token_claims("not a valid token")


# =============== VERIFY_SIGNING_KID ===============
def test_verify_signing_kid_valid(
    valid_access_token: str, valid_user_pool_jwks: List[Dict[str, Any]]
) -> None:
    verify_signing_kid(valid_access_token, valid_user_pool_jwks)


def test_verify_signing_kid_jwt_error(
    valid_user_pool_jwks: List[Dict[str, Any]]
) -> None:
    with pytest.raises(
        SigningKidError, match=r"Validation Failure: token header could not be decoded."
    ):
        verify_signing_kid("invalid token", valid_user_pool_jwks)


def test_verify_signing_kid_jwk_key_error(valid_access_token: str) -> None:
    with pytest.raises(
        SigningKidError,
        match=r"Validation Failure: returned well known JWKs do not all have a `kid` key.",
    ):
        user_pool_jwks_missing_kid_claim: List[Dict[str, Any]] = [
            {"kid": "not_the_access_token_kid_1"},
            {"invalid_key": "not_the_access_token_kid_2"},
        ]
        verify_signing_kid(valid_access_token, user_pool_jwks_missing_kid_claim)


def test_verify_signing_kid_invalid_signing_kid(valid_access_token: str) -> None:
    with pytest.raises(
        SigningKidError,
        match=r"Validation Failure: key id for the token did not match a public key id for the issuer.",
    ):
        user_pool_jwks_missing_access_token_kid: List[Dict[str, Any]] = [
            {"kid": "not_the_access_token_kid_1"},
            {"kid": "not_the_access_token_kid_2"},
        ]
        verify_signing_kid(valid_access_token, user_pool_jwks_missing_access_token_kid)


# =============== VERIFY_CLAIMS ===============
def test_verify_claims_valid(
    valid_id_token: str,
    valid_id_token_kid: Dict[str, Any],
    valid_id_token_claims: Dict[str, Any],
) -> None:
    verify_claims(
        valid_id_token,
        valid_id_token_kid,
        valid_id_token_claims["iss"],
        valid_id_token_claims["aud"],
    )


def test_verify_claims_invalid_iss_error(
    valid_id_token: str,
    valid_id_token_kid: Dict[str, Any],
    valid_id_token_claims: Dict[str, Any],
) -> None:
    with pytest.raises(
        TokenClaimsError,
        match=r"Validation Failure: token issuer is invalid.",
    ):
        verify_claims(
            valid_id_token,
            valid_id_token_kid,
            "incorrect issuer",
            valid_id_token_claims["aud"],
        )


def test_verify_claims_invalid_aud_error(
    valid_id_token: str,
    valid_id_token_kid: Dict[str, Any],
    valid_id_token_claims: Dict[str, Any],
) -> None:
    with pytest.raises(
        TokenClaimsError,
        match=r"Validation Failure: token audience is invalid.",
    ):
        verify_claims(
            valid_id_token,
            valid_id_token_kid,
            valid_id_token_claims["iss"],
            ["incorrect aud"],
        )


def test_verify_claims_incorrect_kid(
    valid_access_token: str,
    valid_id_token_kid: Dict[str, Any],
    valid_access_token_claims: Dict[str, Any],
) -> None:
    with pytest.raises(
        TokenClaimsError,
        match=r"Validation Failure: signature verification failed.",
    ):
        # Mismatch token and JWK to force error
        verify_claims(
            valid_access_token,
            valid_id_token_kid,
            valid_access_token_claims["iss"],
            None,
        )


def test_verify_claims_invalid_key_error(
    valid_access_token: str, valid_access_token_claims: Dict[str, Any]
) -> None:
    with pytest.raises(
        TokenClaimsError,
        match=r"Validation Failure: could not construct public key from token JWK.",
    ):
        verify_claims(
            valid_access_token,
            {"Invalid JWK Key": "Invalid JWK Value"},
            valid_access_token_claims["iss"],
            None,
        )


def test_verify_claims_missing_claims_error(
    invalid_claims_access_token: str,
    invalid_claims_access_token_kid: Dict[str, Any],
    valid_access_token_claims: Dict[str, Any],
) -> None:
    with pytest.raises(
        TokenClaimsError,
        match=r"Validation Failure: token missing required claims.",
    ):
        verify_claims(
            invalid_claims_access_token,
            invalid_claims_access_token_kid,
            valid_access_token_claims["iss"],
            None,
        )


# =============== VERIFY_EXPIRATION ===============
def test_verify_expiration_expired_token() -> None:
    with pytest.raises(ExpirationError, match=r"Validation Failure: token is expired."):
        verify_expiration({"exp": 0})


def test_verify_expiration_key_error() -> None:
    with pytest.raises(
        ExpirationError, match=r"Validation Failure: token is missing exp key."
    ):
        verify_expiration({})


# =============== VERIFY_ALTERNATE_AUD ===============
def test_verify_alternate_aud_valid(
    valid_access_token_claims: Dict[str, Any],
) -> None:
    verify_alternate_aud(
        alternate_aud_key=TEST_ALTERNATE_AUD_KEY,
        known_auds=TEST_KNOWN_AUDS,
        token_claims=valid_access_token_claims,
    )


def test_verify_alternate_aud_missing_claim(
    valid_id_token_claims: Dict[str, Any],
) -> None:
    invalid_claims = valid_id_token_claims.copy()
    invalid_claims.pop("iss")
    with pytest.raises(
        IdPAudError,
        match=r"Validation Failure: token did not have the expected alternate aud key.",
    ):
        verify_alternate_aud(
            alternate_aud_key=TEST_ALTERNATE_AUD_KEY,
            known_auds=TEST_KNOWN_AUDS,
            token_claims=invalid_claims,
        )


def test_verify_alternate_aud_incorrect_aud(
    valid_access_token_claims: Dict[str, Any],
) -> None:
    invalid_claims = valid_access_token_claims.copy()
    invalid_claims[TEST_ALTERNATE_AUD_KEY] = "incorrect-aud-value"
    with pytest.raises(
        IdPAudError,
        match=rf"Validation Failure: {TEST_ALTERNATE_AUD_KEY} was not a known client.",
    ):
        verify_alternate_aud(
            alternate_aud_key=TEST_ALTERNATE_AUD_KEY,
            known_auds=TEST_KNOWN_AUDS,
            token_claims=invalid_claims,
        )


# =============== VERIFY_SCOPE ===============
def test_verify_scope_valid_scope() -> None:
    valid_scope_claims = {"scope": "unknown_scope_1 known_scope_2"}
    known_scopes = ["known_scope_1", "known_scope_2"]
    verify_scope(valid_scope_claims, known_scopes)


def test_verify_scope_invalid_scope() -> None:
    incorrect_scope_claims = {"scope": "invalid-scope-1 invalid-scope-2"}
    known_scopes = ["known_scope_1", "known_scope_2"]
    with pytest.raises(
        ScopeError,
        match=r"Validation Failure: token did not have a known scope.",
    ):
        verify_scope(incorrect_scope_claims, known_scopes)


def test_verify_scope_key_error() -> None:
    known_scopes = ["known_scope_1", "known_scope_2"]
    with pytest.raises(
        ScopeError,
        match=r"Validation Failure: token did not have a scope claim.",
    ):
        verify_scope({"Invalid Key": "Invalid Value"}, known_scopes)
