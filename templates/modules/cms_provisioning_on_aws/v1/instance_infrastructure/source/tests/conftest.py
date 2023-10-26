# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# pylint: disable=W0611

# Connected Mobility Solution on AWS
from .fixtures.fixture_shared import (
    fixture_aws_credentials,
    fixture_context,
    fixture_reset_api_booleans,
    mock_env_vars,
)
from .handlers.fixtures.fixture_custom_resource import (
    fixture_custom_resource_event,
    fixture_custom_resource_load_or_create_iot_credentials_event,
    fixture_custom_resource_update_event_configurations_event,
    fixture_rotate_secret_lambda_function,
)
from .handlers.fixtures.fixture_dynamodb import (
    fixture_mock_dynamodb_resource,
    fixture_setup_authorized_vehicles_table_empty,
    fixture_setup_authorized_vehicles_table_invalid,
    fixture_setup_authorized_vehicles_table_provisioning_allowed,
    fixture_setup_authorized_vehicles_table_provisioning_denied,
    fixture_setup_provisioned_vehicles_table_active,
    fixture_setup_provisioned_vehicles_table_empty,
    fixture_setup_provisioned_vehicles_table_inactive,
    fixture_setup_provisioned_vehicles_table_invalid,
)
from .handlers.fixtures.fixture_initial_connection import (
    fixture_initial_connection_event_invalid,
    fixture_initial_connection_event_valid,
)
from .handlers.fixtures.fixture_post_provision import (
    fixture_post_provision_event,
    fixture_post_provision_event_deleted_event,
    fixture_post_provision_event_no_attributes,
    fixture_post_provision_event_no_template,
)
from .handlers.fixtures.fixture_pre_provision import (
    fixture_authorized_vehicle_allowed,
    fixture_pre_provision_event,
    fixture_pre_provision_event_invalid,
)
from .handlers.fixtures.fixture_rotate_secret import (
    fixture_provisioning_policy,
    fixture_provisioning_secret,
    fixture_provisioning_secret_metadata,
    fixture_provisioning_secret_rotation_enabled,
    fixture_provisioning_secret_staged_for_rotation,
    fixture_rotate_secret_event_invalid_step,
    fixture_rotate_secret_event_invalid_version_to_stage,
    fixture_rotate_secret_event_rotation_not_enabled,
    fixture_rotate_secret_event_valid,
)
from .infrastructure.fixtures.fixture_stack import (
    fixture_auxiliary_lambdas_stack,
    fixture_common_dependencies_stack,
    fixture_iot_provisioning_stack,
    fixture_provisioning_lambdas_stack,
    fixture_snapshot_json_with_matcher,
    fixture_stack,
)
