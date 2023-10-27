# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
from aws_cdk.assertions import Template

# Connected Mobility Solution on AWS
from ....infrastructure.cms_vehicle_simulator_on_aws_stack import (
    InfrastructureSimulatorStack,
)


def test_simulator_role_count(simulator_stack: InfrastructureSimulatorStack) -> None:
    template = Template.from_stack(simulator_stack)
    template.resource_count_is("AWS::IAM::Role", 6)


def test_simulator_policy_count(simulator_stack: InfrastructureSimulatorStack) -> None:
    template = Template.from_stack(simulator_stack)
    template.resource_count_is("AWS::IAM::Policy", 2)


def test_simulator_custom_count(simulator_stack: InfrastructureSimulatorStack) -> None:
    template = Template.from_stack(simulator_stack)
    template.resource_count_is("Custom::AWS", 1)


def test_simulator_lambda_function_count(
    simulator_stack: InfrastructureSimulatorStack,
) -> None:
    template = Template.from_stack(simulator_stack)
    template.resource_count_is("AWS::Lambda::Function", 5)


def test_simulator_log_group_count(
    simulator_stack: InfrastructureSimulatorStack,
) -> None:
    template = Template.from_stack(simulator_stack)
    template.resource_count_is("AWS::Logs::LogGroup", 1)


def test_simulator_state_machine_count(
    simulator_stack: InfrastructureSimulatorStack,
) -> None:
    template = Template.from_stack(simulator_stack)
    template.resource_count_is("AWS::StepFunctions::StateMachine", 1)


def test_simulator_parameter_count(
    simulator_stack: InfrastructureSimulatorStack,
) -> None:
    template = Template.from_stack(simulator_stack)
    template.resource_count_is("AWS::SSM::Parameter", 2)
