#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
from os.path import dirname, realpath

# Third Party Libraries
from aws_cdk import App, Aspects, Environment, Tags
from cdk_nag import AwsSolutionsChecks

# Connected Mobility Solution on AWS
from ..config.constants import BackstageConstants
from .aspects.backstage_nag_suppression import NagSuppression, NagType
from .stacks.stack import BackstageStack

app = App()

if os.environ.get("STACK_TARGET") == BackstageConstants.ENV_APP_NAME:
    # Connected Mobility Solution on AWS
    from .stacks.env import BackstageEnvStack

    config_stack = BackstageEnvStack(
        app,
        BackstageConstants.ENV_APP_NAME,
        env=Environment(
            account=BackstageConstants.AWS_ACCOUNT_ID, region=BackstageConstants.REGION
        ),
        description=(
            f"({BackstageConstants.SOLUTION_ID}-{BackstageConstants.CAPABILITY_ID}) "
            f"{BackstageConstants.SOLUTION_NAME} - Backstage Environment. "
            f"Version {BackstageConstants.SOLUTION_VERSION}"
        ),
    )
else:
    # Connected Mobility Solution on AWS
    from .stacks.stack import BackstageStack  # pylint: disable=reimported

    backstage_stack = BackstageStack(
        app,
        BackstageConstants.STACK_NAME,
        env=Environment(
            account=BackstageConstants.AWS_ACCOUNT_ID, region=BackstageConstants.REGION
        ),
        description=(
            f"({BackstageConstants.SOLUTION_ID}-{BackstageConstants.CAPABILITY_ID}) "
            f"{BackstageConstants.SOLUTION_NAME} - Backstage. "
            f"Version {BackstageConstants.SOLUTION_VERSION}"
        ),
    )

Tags.of(app).add("Solutions:ModuleName", BackstageConstants.MODULE_NAME)
Tags.of(app).add("Solutions:SolutionName", BackstageConstants.SOLUTION_NAME)
Tags.of(app).add("Solutions:SolutionID", BackstageConstants.SOLUTION_ID)
Tags.of(app).add("Solutions:SolutionVersion", BackstageConstants.SOLUTION_VERSION)
Tags.of(app).add("Solutions:ApplicationType", BackstageConstants.APPLICATION_TYPE)


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
