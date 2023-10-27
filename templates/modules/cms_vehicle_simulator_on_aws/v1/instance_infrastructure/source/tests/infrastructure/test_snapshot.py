# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
import aws_cdk
from aws_cdk.assertions import Template
from syrupy.types import SerializableData

# Connected Mobility Solution on AWS
from ...infrastructure.cms_vehicle_simulator_on_aws_stack import (
    CmsVehicleSimulatorOnAwsStack,
    InfrastructureCloudFrontStack,
    InfrastructureCognitoStack,
    InfrastructureConsoleStack,
    InfrastructureGeneralStack,
    InfrastructureResourceStack,
    InfrastructureSimulatorStack,
)


def test_cms_vehicle_simulator_on_aws_snapshot(
    snapshot_json_with_matcher: SerializableData,
) -> None:
    stack = aws_cdk.Stack()
    cms_vehicle_simulator_on_aws_stack = CmsVehicleSimulatorOnAwsStack(
        stack, "cms-vehicle-simulator-on-aws"
    )

    template = Template.from_stack(cms_vehicle_simulator_on_aws_stack)
    assert template.to_json() == snapshot_json_with_matcher


def test_vs_cloudfront_snapshot(snapshot_json_with_matcher: SerializableData) -> None:
    stack = aws_cdk.Stack()
    cloudfront_stack = InfrastructureCloudFrontStack(stack, "vs-cloudfront")  # type: ignore [arg-type]

    template = Template.from_stack(cloudfront_stack)
    assert template.to_json() == snapshot_json_with_matcher


def test_vs_cognito_snapshot(snapshot_json_with_matcher: SerializableData) -> None:
    stack = aws_cdk.Stack()
    cognito_stack = InfrastructureCognitoStack(stack, "vs-cognito")  # type: ignore [arg-type]

    template = Template.from_stack(cognito_stack)
    assert template.to_json() == snapshot_json_with_matcher


def test_vs_general_snapshot(snapshot_json_with_matcher: SerializableData) -> None:
    stack = aws_cdk.Stack()
    general_stack = InfrastructureGeneralStack(
        stack, "vs-general", admin_email="test@test.com"  # type: ignore [arg-type]
    )

    template = Template.from_stack(general_stack)
    assert template.to_json() == snapshot_json_with_matcher


def test_vs_console_snapshot(snapshot_json_with_matcher: SerializableData) -> None:
    stack = aws_cdk.Stack()
    console_stack = InfrastructureConsoleStack(stack, "vs-console")  # type: ignore [arg-type]

    template = Template.from_stack(console_stack)
    assert template.to_json() == snapshot_json_with_matcher


def test_vs_resource_snapshot(snapshot_json_with_matcher: SerializableData) -> None:
    stack = aws_cdk.Stack()
    resource_stack = InfrastructureResourceStack(
        stack, "vs-resource", solution_id="test", solution_version="test"  # type: ignore [arg-type]
    )

    template = Template.from_stack(resource_stack)
    assert template.to_json() == snapshot_json_with_matcher


def test_vs_simulator_snapshot(snapshot_json_with_matcher: SerializableData) -> None:
    stack = aws_cdk.Stack()
    simulator_stack = InfrastructureSimulatorStack(stack, "vs-simulator")  # type: ignore [arg-type]

    template = Template.from_stack(simulator_stack)
    assert template.to_json() == snapshot_json_with_matcher
