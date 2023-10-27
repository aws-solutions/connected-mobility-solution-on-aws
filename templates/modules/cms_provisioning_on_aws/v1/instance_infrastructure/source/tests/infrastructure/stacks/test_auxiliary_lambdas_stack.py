# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library

# Third Party Libraries
from aws_cdk import assertions

# Connected Mobility Solution on AWS
from ....infrastructure.stacks.auxiliary_lambdas_stack import AuxiliaryLambdasStack


def test_role_count(
    auxiliary_lambdas_stack: AuxiliaryLambdasStack,
) -> None:
    template = assertions.Template.from_stack(auxiliary_lambdas_stack)
    template.resource_count_is("AWS::IAM::Role", 3)


def test_lambda_count(
    auxiliary_lambdas_stack: AuxiliaryLambdasStack,
) -> None:
    template = assertions.Template.from_stack(auxiliary_lambdas_stack)
    template.resource_count_is("AWS::Lambda::Function", 3)
