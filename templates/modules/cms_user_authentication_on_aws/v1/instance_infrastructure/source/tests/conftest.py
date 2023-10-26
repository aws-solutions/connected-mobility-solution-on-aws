# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# pylint: disable=W0611


# Connected Mobility Solution on AWS
from .fixtures.fixture_shared import fixture_aws_credentials
from .handlers.fixtures.fixture_create_app_client_lambda import (
    fixture_create_app_client_lambda_event,
)
from .handlers.fixtures.fixture_custom_resource import (
    fixture_custom_resource_event,
    fixture_custom_resource_manage_user_pool_domain_event,
)
from .handlers.fixtures.fixture_delete_app_client_lambda import (
    fixture_delete_app_client_lambda_event,
)
from .handlers.fixtures.fixture_shared import (
    fixture_context,
    fixture_reset_api_booleans,
    mock_env_vars,
)
from .handlers.fixtures.fixture_token_exchange_lambda import (
    fixture_mock_expired_user_pool_tokens,
    fixture_mock_valid_user_pool_tokens,
    fixture_valid_token_exchange_event,
    mock_env_for_token_exchange,
)
from .handlers.fixtures.fixture_token_validation_lambda import (
    fixture_incorrect_key_id_token,
    fixture_invalid_kid_id_token,
    fixture_invalid_scope_service_access_token,
    fixture_invalid_token_validation_event,
    fixture_mock_jwk_construct,
    fixture_mock_user_pool_jwks,
    fixture_token_validation_event_invalid_scope_service_token,
    fixture_token_validation_event_invalid_token,
    fixture_token_validation_event_jwt_error_token,
    fixture_token_validation_event_valid_id_token,
    fixture_token_validation_event_valid_service_token,
    fixture_valid_access_token,
    fixture_valid_access_token_claims,
    fixture_valid_id_token,
    fixture_valid_id_token_claims,
    fixture_valid_service_access_token,
    mock_env_for_token_validation,
)
from .handlers.fixtures.fixture_update_app_client_lambda import (
    fixture_update_app_client_lambda_event,
)
from .infrastructure.fixtures.fixture_stacks import (
    fixture_app_client_lambda_stack,
    fixture_app_registry_stack,
    fixture_cognito_stack,
    fixture_custom_resource_lambda_stack,
    fixture_lambda_dependencies_stack,
    fixture_module_integration_stack,
    fixture_snapshot_json_with_matcher,
    fixture_stack,
    fixture_token_exchange_lambda_stack,
    fixture_token_validation_lambda_stack,
)
