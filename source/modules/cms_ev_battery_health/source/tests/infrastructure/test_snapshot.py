# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
from syrupy.types import SerializableData

# AWS Libraries
from aws_cdk.assertions import Template


def test_cms_ev_battery_health_snapshot(
    snapshot_json_with_matcher: SerializableData,
    ev_battery_health_stack_template: Template,
) -> None:
    assert ev_battery_health_stack_template.to_json() == snapshot_json_with_matcher
