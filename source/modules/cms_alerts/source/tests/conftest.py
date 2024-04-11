# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# pylint: disable=W0611

# Connected Mobility Solution on AWS
from .fixtures.fixture_shared import (
    fixture_aws_credentials_env_vars,
    fixture_context,
    fixture_mock_env_vars,
    fixture_mock_module_env_vars,
)
from .handlers.fixtures.fixture_alerts import fixture_alerts_lambda_event
from .handlers.fixtures.fixture_authorization import (
    fixture_invalid_authorization_event,
    fixture_reset_api_booleans,
    fixture_valid_authorization_event,
    mock_env_for_authorization,
)
from .handlers.fixtures.fixture_publish import fixture_publish_lambda_event
from .handlers.fixtures.fixture_user_subscriptions import (
    fixture_user_subscriptions_create_lambda_event,
    fixture_user_subscriptions_get_lambda_event,
    fixture_user_subscriptions_handler_lambda_event,
    fixture_user_subscriptions_update_lambda_event,
)
from .handlers.fixtures.fixtures_notifications import fixture_notifications_lambda_event
from .infrastructure.fixtures.fixture_stack_templates import (
    fixture_cms_alerts_stack_template,
    fixture_snapshot_json_with_matcher,
)
