#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library

# Third Party Libraries
from aws_cdk import App, Aspects, Tags
from cdk_nag import AwsSolutionsChecks

# Connected Mobility Solution on AWS
from .config.constants import VSConstants
from .infrastructure.aspects.nag_suppression import NagSuppression, NagType
from .infrastructure.cms_vehicle_simulator_on_aws_stack import (
    CmsVehicleSimulatorOnAwsStack,
)

app = App()
stack = CmsVehicleSimulatorOnAwsStack(
    app,
    VSConstants.APP_NAME,
    stack_name=VSConstants.APP_NAME,
    description=(
        f"({VSConstants.SOLUTION_ID}-{VSConstants.CAPABILITY_ID}) "
        f"{VSConstants.SOLUTION_NAME} - Vehicle Simulator. "
        f"Version {VSConstants.SOLUTION_VERSION}"
    ),
)

# Tags
Tags.of(app).add("Solutions:ModuleName", VSConstants.MODULE_NAME)
Tags.of(app).add("Solutions:SolutionName", VSConstants.SOLUTION_NAME)
Tags.of(app).add("Solutions:SolutionID", VSConstants.SOLUTION_ID)
Tags.of(app).add("Solutions:SolutionVersion", VSConstants.SOLUTION_VERSION)
Tags.of(app).add("Solutions:ApplicationType", VSConstants.APPLICATION_TYPE)

# Aspects
Aspects.of(app).add(NagSuppression(".cdk-nag-suppression-list.json", NagType.CDK_NAG))
Aspects.of(app).add(NagSuppression(".cfn-nag-suppression-list.json", NagType.CFN_NAG))
if app.node.try_get_context("nag-enforce"):
    Aspects.of(app).add(AwsSolutionsChecks())

app.synth()
