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
from .handlers.fixtures.fixture_vehicle_trigger_alarm import (
    fixture_auth_client_config_secret_string_valid,
    fixture_mock_boto_client_config_valid,
    fixture_vehicle_trigger_alarm_clear_lru_caches,
    fixture_vehicle_trigger_alarm_environment_valid,
    fixture_vehicle_trigger_alarm_event,
)
from .infrastructure.fixtures.fixture_stack_templates import (
    fixture_cms_connect_store_stack_template,
    fixture_snapshot_json_with_matcher,
)
