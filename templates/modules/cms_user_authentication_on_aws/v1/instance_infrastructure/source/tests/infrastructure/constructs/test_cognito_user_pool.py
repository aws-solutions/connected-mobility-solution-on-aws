# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
from aws_cdk import Stack, assertions


def test_cognito_userpool(cognito_stack: Stack) -> None:
    template = assertions.Template.from_stack(cognito_stack)
    template.resource_count_is("AWS::Cognito::UserPool", 1)


def test_user_pool_client(cognito_stack: Stack) -> None:
    template = assertions.Template.from_stack(cognito_stack)
    template.resource_count_is("AWS::Cognito::UserPoolClient", 2)


def test_user_pool_resource(cognito_stack: Stack) -> None:
    template = assertions.Template.from_stack(cognito_stack)
    template.resource_count_is("AWS::Cognito::UserPoolResourceServer", 1)


def test_policy(cognito_stack: Stack) -> None:
    template = assertions.Template.from_stack(cognito_stack)
    template.resource_count_is("AWS::IAM::Policy", 4)


def test_manage_user_pool_domain(cognito_stack: Stack) -> None:
    template = assertions.Template.from_stack(cognito_stack)
    template.resource_count_is("Custom::ManageUserPoolDomain", 1)
