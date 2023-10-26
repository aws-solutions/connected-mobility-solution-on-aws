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
from .config.constants import VPConstants
from .infrastructure.aspects.nag_suppression import NagSuppression
from .infrastructure.cms_provisioning_on_aws_stack import CmsProvisioningOnAwsStack
from .infrastructure.lib.nag_type_enum import NagType

app = App()
stack = CmsProvisioningOnAwsStack(
    app,
    VPConstants.APP_NAME,
    stack_name=VPConstants.APP_NAME,
    description=(
        f"({VPConstants.SOLUTION_ID}-{VPConstants.CAPABILITY_ID}) "
        f"{VPConstants.SOLUTION_NAME} - Provisioning. "
        f"Version {VPConstants.SOLUTION_VERSION}"
    ),
)

# Tags
Tags.of(app).add("Solutions:ModuleName", VPConstants.MODULE_NAME)
Tags.of(app).add("Solutions:SolutionName", VPConstants.SOLUTION_NAME)
Tags.of(app).add("Solutions:SolutionID", VPConstants.SOLUTION_ID)
Tags.of(app).add("Solutions:SolutionVersion", VPConstants.SOLUTION_VERSION)
Tags.of(app).add("Solutions:ApplicationType", VPConstants.APPLICATION_TYPE)

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
