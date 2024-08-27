# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# pylint: disable=unused-import

# Connected Mobility Solution on AWS
from .fixtures.fixture_boto3 import (
    fixture_mock_boto3_client,
    fixture_ssm_stubber,
    fixture_timestream_stubber,
)
from .fixtures.fixture_shared import (
    fixture_aws_credentials_env_vars,
    fixture_mock_env_vars,
    fixture_mock_module_env_vars,
)
from .infrastructure.fixtures.fixture_stack_templates import (
    fixture_cms_fleetwise_connector_stack_template,
    fixture_snapshot_json_with_matcher,
)
