# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# pylint: disable=W0611

# Connected Mobility Solution on AWS
from .handlers.fixtures.fixture_custom_resource import (
    fixture_context,
    fixture_custom_resource_create_deployment_uuid_event,
    fixture_custom_resource_create_event,
    fixture_custom_resource_event,
)
from .handlers.fixtures.fixtures_shared import fixture_aws_credentials
