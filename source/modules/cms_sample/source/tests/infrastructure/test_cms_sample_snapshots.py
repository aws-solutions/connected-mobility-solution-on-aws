# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
from syrupy.types import SerializableData

# AWS Libraries
import aws_cdk
from aws_cdk.assertions import Template

# CMS Common Library
from cms_common.config.stack_inputs import S3AssetConfigInputs, SolutionConfigInputs

# Connected Mobility Solution on AWS
from ...infrastructure.cms_sample_stack import CmsSampleStack


def test_cms_sample_snapshot(
    snapshot_json_with_matcher: SerializableData,
) -> None:
    solution_config_inputs = SolutionConfigInputs(
        solution_id="test-solution-id",
        solution_name="test-solution-name",
        solution_version="test-solution-version",
        application_type="test-application-type",
        module_name="test-module-name",
        module_short_name="test-module-short-name",
        capability_id="test-capability-id",
    )
    s3_asset_config_inputs = S3AssetConfigInputs(
        bucket_base_name="test-bucket-base-name",
        object_key_prefix="test-object-key-prefix",
    )
    stack = aws_cdk.Stack()
    cms_sample_stack = CmsSampleStack(
        stack,
        "cms-sample",
        solution_config_inputs=solution_config_inputs,
        s3_asset_config_inputs=s3_asset_config_inputs,
    )

    template = Template.from_stack(cms_sample_stack)
    assert template.to_json() == snapshot_json_with_matcher
