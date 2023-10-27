#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from os.path import dirname, realpath

# Third Party Libraries
from aws_cdk import App, Aspects, Tags
from cdk_nag import AwsSolutionsChecks

# Connected Mobility Solution on AWS
from .config.constants import APIConstants
from .infrastructure.aspects.nag_suppression import NagSuppression
from .infrastructure.cms_api_on_aws_stack import CmsAPIOnAwsStack
from .infrastructure.lib.nag_type_enum import NagType

app = App()
stack = CmsAPIOnAwsStack(
    app,
    APIConstants.APP_NAME,
    stack_name=APIConstants.APP_NAME,
    description=(
        f"({APIConstants.SOLUTION_ID}-{APIConstants.CAPABILITY_ID}) "
        f"{APIConstants.SOLUTION_NAME} - API. "
        f"Version {APIConstants.SOLUTION_VERSION}"
    ),
)

# Tags
Tags.of(app).add("Solutions:ModuleName", APIConstants.MODULE_NAME)
Tags.of(app).add("Solutions:SolutionName", APIConstants.SOLUTION_NAME)
Tags.of(app).add("Solutions:SolutionID", APIConstants.SOLUTION_ID)
Tags.of(app).add("Solutions:SolutionVersion", APIConstants.SOLUTION_VERSION)
Tags.of(app).add("Solutions:ApplicationType", APIConstants.APPLICATION_TYPE)

# Aspects
Aspects.of(app).add(
    NagSuppression(
        f"{dirname(realpath(__file__))}/.cdk-nag-suppression-list.json", NagType.CDK_NAG
    )
)
Aspects.of(app).add(
    NagSuppression(
        f"{dirname(realpath(__file__))}/.cfn-nag-suppression-list.json", NagType.CFN_NAG
    )
)
if app.node.try_get_context("nag-enforce"):
    Aspects.of(app).add(AwsSolutionsChecks())

app.synth()
