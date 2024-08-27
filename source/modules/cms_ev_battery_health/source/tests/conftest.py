# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# pylint: disable=unused-import

# Connected Mobility Solution on AWS
from .fixtures.fixture_custom_resource import (
    fixture_custom_resource_create_grafana_alerts_and_upload_to_s3_event,
    fixture_custom_resource_create_grafana_api_key_event,
    fixture_custom_resource_create_grafana_dashboard_and_upload_to_s3_event,
    fixture_custom_resource_create_grafana_data_source_event,
    fixture_custom_resource_enable_grafana_alerting_event,
    fixture_custom_resource_event,
    fixture_custom_resource_install_grafana_plugin_event,
    fixture_custom_resource_set_grafana_alert_configuration_event,
)
from .fixtures.fixture_process_alerts import (
    fixture_auth_client_config_secret_string_valid,
    fixture_auth_idp_config_secret_string_valid,
    fixture_mock_boto_client_config_valid,
    fixture_mock_boto_idp_config_valid,
    fixture_mock_process_alerts_environment_valid,
    fixture_process_alerts_clear_lru_caches,
    fixture_process_alerts_event,
)
from .fixtures.fixture_rotate_secret import (
    fixture_grafana_api_key_secret_rotation_enabled,
    fixture_grafana_api_key_secret_staged_for_rotation,
    fixture_rotate_secret_event_invalid_step,
    fixture_rotate_secret_event_invalid_version_to_stage,
    fixture_rotate_secret_event_rotation_not_enabled,
    fixture_rotate_secret_event_valid,
    fixture_rotate_secret_lambda_function,
)
from .fixtures.fixture_s3_to_grafana import (
    fixture_s3_to_grafana_alerts_event,
    fixture_s3_to_grafana_dashboard_event,
)
from .fixtures.fixture_shared import (
    fixture_aws_credentials_env_vars,
    fixture_context,
    fixture_grafana_api_key_secret,
    fixture_grafana_api_key_secret_metadata,
    fixture_mock_env_vars,
    fixture_mock_module_env_vars,
    fixture_s3_dashboard_bucket,
)
from .fixtures.fixture_stack_templates import (
    fixture_ev_battery_health_stack_template,
    fixture_snapshot_json_with_matcher,
)
