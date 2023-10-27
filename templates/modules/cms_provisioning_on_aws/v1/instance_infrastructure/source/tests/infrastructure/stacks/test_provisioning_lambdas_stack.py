# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library

# Third Party Libraries
from aws_cdk import assertions

# Connected Mobility Solution on AWS
from ....infrastructure.stacks.provisioning_lambdas_stack import (
    ProvisioningLambdasStack,
)


def test_role_count(
    provisioning_lambdas_stack: ProvisioningLambdasStack,
) -> None:
    template = assertions.Template.from_stack(provisioning_lambdas_stack)
    template.resource_count_is("AWS::IAM::Role", 4)


def test_lambda_count(
    provisioning_lambdas_stack: ProvisioningLambdasStack,
) -> None:
    template = assertions.Template.from_stack(provisioning_lambdas_stack)
    template.resource_count_is("AWS::Lambda::Function", 4)


def test_dynamodb_table_count(
    provisioning_lambdas_stack: ProvisioningLambdasStack,
) -> None:
    template = assertions.Template.from_stack(provisioning_lambdas_stack)
    template.resource_count_is("AWS::DynamoDB::Table", 2)


def test_iot_rule_count(
    provisioning_lambdas_stack: ProvisioningLambdasStack,
) -> None:
    template = assertions.Template.from_stack(provisioning_lambdas_stack)
    template.resource_count_is("AWS::IoT::TopicRule", 2)
