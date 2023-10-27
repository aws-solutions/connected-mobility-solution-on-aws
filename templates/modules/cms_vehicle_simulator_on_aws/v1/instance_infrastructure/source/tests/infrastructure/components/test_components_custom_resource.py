# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
from aws_cdk.assertions import Template

# Connected Mobility Solution on AWS
from ....infrastructure.cms_vehicle_simulator_on_aws_stack import (
    InfrastructureResourceStack,
)


def test_custom_resource_role_count(
    custom_resource_stack: InfrastructureResourceStack,
) -> None:
    template = Template.from_stack(custom_resource_stack)
    template.resource_count_is("AWS::IAM::Role", 2)


def test_custom_resource_lambda_function_count(
    custom_resource_stack: InfrastructureResourceStack,
) -> None:
    template = Template.from_stack(custom_resource_stack)
    template.resource_count_is("AWS::Lambda::Function", 2)


def test_custom_resource_count(
    custom_resource_stack: InfrastructureResourceStack,
) -> None:
    template = Template.from_stack(custom_resource_stack)
    template.resource_count_is("AWS::CloudFormation::CustomResource", 1)


def test_custom_resource_create_pool_user_count(
    custom_resource_stack: InfrastructureResourceStack,
) -> None:
    template = Template.from_stack(custom_resource_stack)
    template.resource_count_is("Custom::CreateUserpoolUser", 1)
