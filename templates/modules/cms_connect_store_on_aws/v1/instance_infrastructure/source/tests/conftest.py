# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# pylint: disable=W0611

# Connected Mobility Solution on AWS
from .fixtures.fixture_shared import (
    fixture_aws_credentials_env_vars,
    fixture_context,
    fixture_service_client_credentials_secret,
)
from .handlers.fixtures.fixture_vehicle_trigger_alarm import (
    fixture_vehicle_trigger_alarm_event,
)
from .infrastructure.fixtures.fixture_stack import fixture_snapshot_json_with_matcher
