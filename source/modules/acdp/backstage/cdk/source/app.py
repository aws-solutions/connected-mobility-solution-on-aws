#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
from os.path import dirname, realpath

# AWS Libraries
from aws_cdk import App, Aspects, DefaultStackSynthesizer, Environment
from cdk_nag import AwsSolutionsChecks

# Connected Mobility Solution on AWS
from .infrastructure.acdp_backstage_stack import AcdpBackstageStack
from .infrastructure.aspects.backstage_nag_suppression import NagSuppression, NagType
from .infrastructure.lib.cms_common.aspects.vpc_aspect import ApplyVpcOnCustomResource
from .infrastructure.lib.cms_common.config.stack_inputs import (
    S3AssetConfigInputs,
    SolutionConfigInputs,
    create_solution_tags_for_stack,
    create_stack_description,
)

solution_config_inputs = SolutionConfigInputs(
    solution_id=os.environ["SOLUTION_ID"],
    solution_name=os.environ["SOLUTION_NAME"],
    solution_version=os.environ["SOLUTION_VERSION"],
    application_type=os.environ["APPLICATION_TYPE"],
    module_name=os.environ["MODULE_NAME"],
    module_short_name=os.environ["MODULE_SHORT_NAME"],
    capability_id=os.environ["CAPABILITY_ID"],
)

# The bucket_base_name is unused and instead replaced by s3_asset_bucket_name in backstage because
# cdk synth occurs in the deployment account to a local acdp owned bucket
s3_asset_config_inputs = S3AssetConfigInputs(
    bucket_base_name="UNUSED",
    object_key_prefix=os.environ["S3_ASSET_KEY_PREFIX"],
)
s3_asset_bucket_name = os.environ["LOCAL_ASSET_BUCKET_NAME"]

app = App()

backstage_stack = AcdpBackstageStack(
    app,
    solution_config_inputs.module_name,
    description=create_stack_description(solution_config=solution_config_inputs),
    solution_config_inputs=solution_config_inputs,
    s3_asset_config_inputs=s3_asset_config_inputs,
    s3_asset_bucket_name=s3_asset_bucket_name,
    env=Environment(
        account=os.environ["AWS_ACCOUNT_ID"], region=os.environ["AWS_REGION"]
    ),
    synthesizer=DefaultStackSynthesizer(generate_bootstrap_version_rule=False),
)

create_solution_tags_for_stack(app, solution_config=solution_config_inputs)

# Aspects
Aspects.of(app).add(
    ApplyVpcOnCustomResource(
        module_name=solution_config_inputs.module_name,
        security_group_logical_ids=backstage_stack.backstage_construct.cdk_lambdas_vpc_construct.security_groups,
        subnet_names=backstage_stack.backstage_construct.cdk_lambdas_vpc_construct.subnets,
    )
)


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
if os.environ.get("CDK_NAG_ENFORCE") == "true":
    Aspects.of(app).add(AwsSolutionsChecks())

app.synth()
