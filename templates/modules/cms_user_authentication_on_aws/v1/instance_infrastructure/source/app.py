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
from .config.constants import UserAuthenticationConstants
from .infrastructure.aspects.nag_suppression import NagSuppression
from .infrastructure.cms_user_authentication_on_aws_stack import (
    CmsUserAuthenticationOnAwsStack,
)
from .infrastructure.lib.nag_type_enum import NagType

app = App()
stack = CmsUserAuthenticationOnAwsStack(
    app,
    UserAuthenticationConstants.APP_NAME,
    stack_name=UserAuthenticationConstants.APP_NAME,
    description=(
        f"({UserAuthenticationConstants.SOLUTION_ID}-{UserAuthenticationConstants.CAPABILITY_ID}) "
        f"{UserAuthenticationConstants.SOLUTION_NAME} - User Authentication. "
        f"Version {UserAuthenticationConstants.SOLUTION_VERSION}"
    ),
)

# Tags
Tags.of(app).add("Solutions:ModuleName", UserAuthenticationConstants.MODULE_NAME)
Tags.of(app).add("Solutions:SolutionName", UserAuthenticationConstants.SOLUTION_NAME)
Tags.of(app).add("Solutions:SolutionID", UserAuthenticationConstants.SOLUTION_ID)
Tags.of(app).add(
    "Solutions:SolutionVersion", UserAuthenticationConstants.SOLUTION_VERSION
)
Tags.of(app).add(
    "Solutions:ApplicationType", UserAuthenticationConstants.APPLICATION_TYPE
)

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
