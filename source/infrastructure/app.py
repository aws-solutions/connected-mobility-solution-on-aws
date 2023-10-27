#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from os.path import dirname, realpath

# Third Party Libraries
import aws_cdk
from cdk_nag import AwsSolutionsChecks

# Connected Mobility Solution on AWS
from .aspects.nag_suppression import NagSuppression, NagType
from .stacks import CmsConstants
from .stacks.cms_stack import CmsStack

app = aws_cdk.App()
stack = CmsStack(
    app,
    CmsConstants.STACK_NAME,
    description=(
        f"({CmsConstants.SOLUTION_ID}) "
        f"{CmsConstants.SOLUTION_NAME}. "
        f"Version {CmsConstants.SOLUTION_VERSION}"
    ),
)


aws_cdk.Tags.of(app).add("Solutions:ModuleName", CmsConstants.MODULE_NAME)
aws_cdk.Tags.of(app).add("Solutions:SolutionName", CmsConstants.SOLUTION_NAME)
aws_cdk.Tags.of(app).add("Solutions:SolutionID", CmsConstants.SOLUTION_ID)
aws_cdk.Tags.of(app).add("Solutions:SolutionVersion", CmsConstants.SOLUTION_VERSION)
aws_cdk.Tags.of(app).add("Solutions:ApplicationType", CmsConstants.APPLICATION_TYPE)

# CDK and CFN nags
aws_cdk.Aspects.of(app).add(
    NagSuppression(
        f"{dirname(realpath(__file__))}/.cdk-nag-suppression-list.json", NagType.CDK_NAG
    )
)
aws_cdk.Aspects.of(app).add(
    NagSuppression(
        f"{dirname(realpath(__file__))}/.cfn-nag-suppression-list.json", NagType.CFN_NAG
    )
)
if app.node.try_get_context("nag-enforce"):
    aws_cdk.Aspects.of(app).add(AwsSolutionsChecks())

app.synth()
