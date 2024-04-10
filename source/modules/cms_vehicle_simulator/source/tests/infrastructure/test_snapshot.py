# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
from syrupy.types import SerializableData

# AWS Libraries
from aws_cdk.assertions import Template

# Connected Mobility Solution on AWS
from ...infrastructure.cms_vehicle_simulator_stack import CmsVehicleSimulatorStack


def test_cms_vehicle_simulator_snapshot(
    snapshot_json_with_matcher: SerializableData,
    cms_vehicle_simulator_stack: CmsVehicleSimulatorStack,
) -> None:
    template = Template.from_stack(cms_vehicle_simulator_stack)
    assert template.to_json() == snapshot_json_with_matcher
