# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# pylint: disable=unused-import

# Connected Mobility Solution on AWS
from .fixtures.fixtures_shared import (
    fixture_aws_credentials_env_vars,
    fixture_mock_env_vars,
    fixture_mock_module_env_vars,
)
from .handlers.fixtures.fixture_custom_resource import (
    fixture_context,
    fixture_custom_resource_create_deployment_uuid_event,
    fixture_custom_resource_event,
)
from .infrastructure.fixtures.fixture_stack_templates import (
    fixture_acdp_stack_parameters,
    fixture_acdp_stack_template,
    fixture_snapshot_json_with_matcher,
)
