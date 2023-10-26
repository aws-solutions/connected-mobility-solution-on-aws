# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
from aws_cdk import Stack, assertions


def test_lambda_function(app_client_lambda_stack: Stack) -> None:
    template = assertions.Template.from_stack(app_client_lambda_stack)
    template.resource_count_is("AWS::Lambda::Function", 2)


def test_iam_role(app_client_lambda_stack: Stack) -> None:
    template = assertions.Template.from_stack(app_client_lambda_stack)
    template.resource_count_is("AWS::IAM::Role", 2)


def test_iam_policy(app_client_lambda_stack: Stack) -> None:
    template = assertions.Template.from_stack(app_client_lambda_stack)
    template.resource_count_is("AWS::IAM::Policy", 1)
