# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
import aws_cdk

# Connected Mobility Solution on AWS
from ...infrastructure.cms_environment_on_aws_stack import CmsEnvironmentOnAwsStack
from ...config.constants import EnvironmentConstants

app = aws_cdk.App()
stack = CmsEnvironmentOnAwsStack(
    app,
    EnvironmentConstants.APP_NAME,
    env=aws_cdk.Environment(
        account="test-account-id",
        region="us-west-2",
    ),
)
template = aws_cdk.assertions.Template.from_stack(stack)


def test_iam_role() -> None:
    template.has_resource("AWS::IAM::Role", {})
    template.resource_count_is("AWS::IAM::Role", 1)


def test_iot_logging() -> None:
    template.has_resource("AWS::IoT::Logging", {})
    template.resource_count_is("AWS::IoT::Logging", 1)
