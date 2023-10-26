# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
from aws_cdk.assertions import Template

# Connected Mobility Solution on AWS
from ....infrastructure.cms_vehicle_simulator_on_aws_stack import (
    InfrastructureGeneralStack,
)


def test_general_ssm_parameter_count(general_stack: InfrastructureGeneralStack) -> None:
    template = Template.from_stack(general_stack)
    template.resource_count_is("AWS::SSM::Parameter", 8)


def test_general_dynamodb_table_count(
    general_stack: InfrastructureGeneralStack,
) -> None:
    template = Template.from_stack(general_stack)
    template.resource_count_is("AWS::DynamoDB::Table", 3)


def test_general_lambda_layer_count(general_stack: InfrastructureGeneralStack) -> None:
    template = Template.from_stack(general_stack)
    template.resource_count_is("AWS::Lambda::LayerVersion", 1)
