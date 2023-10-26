# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library

# Third Party Libraries
from aws_cdk import Stack, assertions


def test_role_count(
    token_exchange_lambda_stack: Stack,
) -> None:
    template = assertions.Template.from_stack(token_exchange_lambda_stack)
    template.resource_count_is("AWS::IAM::Role", 2)


def test_lambda_count(
    token_exchange_lambda_stack: Stack,
) -> None:
    template = assertions.Template.from_stack(token_exchange_lambda_stack)
    template.resource_count_is("AWS::Lambda::Function", 2)
