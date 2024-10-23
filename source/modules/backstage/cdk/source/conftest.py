# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0


# pylint: disable=unused-import

# Standard Library
from unittest.mock import patch

# Third Party Libraries
import pytest

# Connected Mobility Solution on AWS
from .tests.infrastructure.fixtures.fixture_stack_templates import (
    fixture_acdp_backstage_stack_template,
    fixture_snapshot_json_with_matcher,
)
