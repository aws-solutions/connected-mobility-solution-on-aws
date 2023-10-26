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
from .config.constants import EVBatteryHealthConstants
from .infrastructure.aspects.nag_suppression import NagSuppression
from .infrastructure.cms_ev_battery_health_on_aws_stack import (
    CmsEVBatteryHealthOnAwsStack,
)
from .infrastructure.lib.nag_type_enum import NagType

app = App()
stack = CmsEVBatteryHealthOnAwsStack(
    app,
    EVBatteryHealthConstants.APP_NAME,
    stack_name=EVBatteryHealthConstants.APP_NAME,
    description=(
        f"({EVBatteryHealthConstants.SOLUTION_ID}-{EVBatteryHealthConstants.CAPABILITY_ID}) "
        f"{EVBatteryHealthConstants.SOLUTION_NAME} - EV Battery Health. "
        f"Version {EVBatteryHealthConstants.SOLUTION_VERSION}"
    ),
)

# Tags
Tags.of(app).add("Solutions:ModuleName", EVBatteryHealthConstants.MODULE_NAME)
Tags.of(app).add("Solutions:SolutionName", EVBatteryHealthConstants.SOLUTION_NAME)
Tags.of(app).add("Solutions:SolutionID", EVBatteryHealthConstants.SOLUTION_ID)
Tags.of(app).add("Solutions:SolutionVersion", EVBatteryHealthConstants.SOLUTION_VERSION)
Tags.of(app).add("Solutions:ApplicationType", EVBatteryHealthConstants.APPLICATION_TYPE)

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
