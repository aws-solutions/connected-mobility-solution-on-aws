# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
import aws_cdk as core
from aws_cdk import assertions

# Connected Mobility Solution on AWS
from ...source.infrastructure.cms_environment_on_aws_stack import (
    CmsEnvironmentOnAwsStack,
)


def test_iam_role() -> None:
    app = core.App()
    stack = CmsEnvironmentOnAwsStack(app, "cms_environment")
    template = assertions.Template.from_stack(stack)

    template.resource_count_is("AWS::IAM::Role", 1)
