# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# pylint: disable=unused-import

# Connected Mobility Solution on AWS
from .fixtures.fixture_shared import (
    fixture_aws_credentials_env_vars,
    fixture_context,
    fixture_mock_env_vars,
    fixture_mock_module_env_vars,
    fixture_reset_api_booleans,
)
from .handlers.fixtures.fixture_athena_data_source import (
    fixture_athena_data_source_lambda_event,
    fixture_unproccessed_athena_query_results,
)
from .handlers.fixtures.fixture_authorization import (
    fixture_invalid_authorization_event,
    fixture_valid_authorization_event,
    mock_env_for_authorization,
)
from .infrastructure.fixtures.fixture_stack_templates import (
    fixture_cms_api_stack_template,
    fixture_snapshot_json_with_matcher,
)
