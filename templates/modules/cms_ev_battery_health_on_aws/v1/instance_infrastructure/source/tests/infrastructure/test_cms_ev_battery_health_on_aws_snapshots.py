# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
import aws_cdk
from aws_cdk.assertions import Template
from syrupy.types import SerializableData

# Connected Mobility Solution on AWS
from ...infrastructure.cms_ev_battery_health_on_aws_stack import (
    CmsEVBatteryHealthOnAwsStack,
)


def test_cms_ev_battery_health_on_aws_snapshot(
    snapshot_json_with_matcher: SerializableData,
) -> None:
    stack = aws_cdk.Stack()
    cms_ev_battery_health_on_aws_stack = CmsEVBatteryHealthOnAwsStack(
        stack, "cms-ev-battery-health-on-aws-stack"
    )

    template = Template.from_stack(cms_ev_battery_health_on_aws_stack)
    assert template.to_json() == snapshot_json_with_matcher
