# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
from aws_cdk.assertions import Template

# Connected Mobility Solution on AWS
from ....infrastructure.cms_vehicle_simulator_on_aws_stack import (
    InfrastructureConsoleStack,
)


def test_console_role_count(console_stack: InfrastructureConsoleStack) -> None:
    template = Template.from_stack(console_stack)
    template.resource_count_is("AWS::IAM::Role", 2)


def test_console_policy_count(console_stack: InfrastructureConsoleStack) -> None:
    template = Template.from_stack(console_stack)
    template.resource_count_is("AWS::IAM::Policy", 1)


def test_console_lambda_function_count(
    console_stack: InfrastructureConsoleStack,
) -> None:
    template = Template.from_stack(console_stack)
    template.resource_count_is("AWS::Lambda::Function", 1)


def test_console_lambda_layer_count(console_stack: InfrastructureConsoleStack) -> None:
    template = Template.from_stack(console_stack)
    template.resource_count_is("AWS::Lambda::LayerVersion", 1)


def test_console_location_map_count(console_stack: InfrastructureConsoleStack) -> None:
    template = Template.from_stack(console_stack)
    template.resource_count_is("AWS::Location::Map", 1)


def test_console_location_place_index_count(
    console_stack: InfrastructureConsoleStack,
) -> None:
    template = Template.from_stack(console_stack)
    template.resource_count_is("AWS::Location::PlaceIndex", 1)


def test_console_cognito_attachement_count(
    console_stack: InfrastructureConsoleStack,
) -> None:
    template = Template.from_stack(console_stack)
    template.resource_count_is("AWS::Cognito::IdentityPoolRoleAttachment", 1)


def test_console_iot_policy_count(console_stack: InfrastructureConsoleStack) -> None:
    template = Template.from_stack(console_stack)
    template.resource_count_is("AWS::IoT::Policy", 1)


def test_console_custom_bucket_count(console_stack: InfrastructureConsoleStack) -> None:
    template = Template.from_stack(console_stack)
    template.resource_count_is("Custom::CDKBucketDeployment", 1)


def test_console_custom_config_count(console_stack: InfrastructureConsoleStack) -> None:
    template = Template.from_stack(console_stack)
    template.resource_count_is("Custom::CopyConfigFiles", 1)


def test_console_custom_resource_count(
    console_stack: InfrastructureConsoleStack,
) -> None:
    template = Template.from_stack(console_stack)
    template.resource_count_is("AWS::CloudFormation::CustomResource", 1)
