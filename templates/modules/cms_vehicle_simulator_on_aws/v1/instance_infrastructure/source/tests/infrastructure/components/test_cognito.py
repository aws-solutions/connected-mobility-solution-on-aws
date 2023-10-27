# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
from aws_cdk.assertions import Template

# Connected Mobility Solution on AWS
from ....infrastructure.cms_vehicle_simulator_on_aws_stack import (
    InfrastructureCognitoStack,
)


def test_cognito_userpool_count(cognito_stack: InfrastructureCognitoStack) -> None:
    template = Template.from_stack(cognito_stack)
    template.resource_count_is("AWS::Cognito::UserPool", 1)


def test_cognito_userpool_client_count(
    cognito_stack: InfrastructureCognitoStack,
) -> None:
    template = Template.from_stack(cognito_stack)
    template.resource_count_is("AWS::Cognito::UserPoolClient", 1)


def test_cognito_identity_pool_count(cognito_stack: InfrastructureCognitoStack) -> None:
    template = Template.from_stack(cognito_stack)
    template.resource_count_is("AWS::Cognito::IdentityPool", 1)
