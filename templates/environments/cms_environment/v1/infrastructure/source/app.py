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
from .config.constants import EnvironmentConstants
from .infrastructure.aspects.nag_suppression import NagSuppression, NagType
from .infrastructure.cms_environment_on_aws_stack import CmsEnvironmentOnAwsStack

app = aws_cdk.App()
CmsEnvironmentOnAwsStack(
    app, 
    "cms-environment",
    description=(
        f"({EnvironmentConstants.SOLUTION_ID}-{EnvironmentConstants.CAPABILITY_ID}) "
        f"{EnvironmentConstants.SOLUTION_NAME} - Backstage Environment. "
        f"Version {EnvironmentConstants.SOLUTION_VERSION}"
    ),
)

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
