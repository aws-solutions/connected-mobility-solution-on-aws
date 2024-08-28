# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# pylint: disable=unused-import

# Connected Mobility Solution on AWS
from .fixtures.fixture_shared import (
    fixture_aws_credentials_env_vars,
    fixture_mock_env_vars,
    fixture_mock_module_env_vars,
)
from .handlers.fixtures.fixture_authorization_code_exchange_lambda import (
    fixture_authorization_code_exchange_clear_lru_caches,
    fixture_authorization_code_exchange_event_valid,
    fixture_idp_config_secret_string_valid,
    fixture_mock_authorization_code_exchange_environment_valid,
    fixture_mock_idp_config_valid,
    fixture_mock_token_endpoint_valid_tokens,
    fixture_mock_user_client_config_invalid_json,
    fixture_mock_user_client_config_valid,
    fixture_user_client_config_secret_string_valid,
)
from .handlers.fixtures.fixture_shared import fixture_context
from .handlers.fixtures.fixture_token_validation_lambda import (
    fixture_expired_access_token,
    fixture_incorrect_key_id_token,
    fixture_invalid_claims_access_token,
    fixture_invalid_claims_access_token_kid,
    fixture_invalid_kid_id_token,
    fixture_invalid_scope_service_access_token,
    fixture_mock_jwk_construct,
    fixture_mock_token_validation_environment_valid,
    fixture_mock_token_validation_idp_config_valid,
    fixture_mock_well_known_jwks_decode_error,
    fixture_mock_well_known_jwks_invalid_key_error,
    fixture_mock_well_known_jwks_unknown_jwks,
    fixture_mock_well_known_jwks_valid,
    fixture_token_validation_clear_lru_caches,
    fixture_token_validation_event_expired_token,
    fixture_token_validation_event_incorrect_kid_token,
    fixture_token_validation_event_invalid_exp_token,
    fixture_token_validation_event_invalid_scope_service_token,
    fixture_token_validation_event_invalid_token,
    fixture_token_validation_event_invalid_token_claims,
    fixture_token_validation_event_valid_access_token,
    fixture_token_validation_event_valid_id_token,
    fixture_token_validation_event_valid_service_token,
    fixture_token_validation_idp_config_secret_string_valid,
    fixture_valid_access_token,
    fixture_valid_access_token_claims,
    fixture_valid_id_token,
    fixture_valid_id_token_claims,
    fixture_valid_id_token_kid,
    fixture_valid_service_access_token,
    fixture_valid_user_pool_jwks,
)
from .infrastructure.fixtures.fixture_stack_templates import (
    fixture_cms_auth_stack_template,
    fixture_snapshot_json_with_matcher,
)
