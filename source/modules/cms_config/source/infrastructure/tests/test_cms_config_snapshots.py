# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import tempfile
from unittest.mock import MagicMock

# Third Party Libraries
from syrupy.types import SerializableData

# AWS Libraries
from aws_cdk import Stack, assertions, aws_lambda

# CMS Common Library
from cms_common.config.stack_inputs import S3AssetConfigInputs, SolutionConfigInputs

# Connected Mobility Solution on AWS
from ...infrastructure.cms_config_stack import CmsConfigStack


def test_cms_config_snapshot(
    snapshot_json_with_matcher: SerializableData,
) -> None:
    with tempfile.TemporaryDirectory() as tmpdirname:
        # mock lambda code asset path
        aws_lambda.Code.from_asset = MagicMock(  # type: ignore[method-assign]
            return_value=aws_lambda.AssetCode(path=tmpdirname)
        )

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
        stack = Stack()
        cms_config_stack = CmsConfigStack(
            stack,
            "cms-config",
            solution_config_inputs=solution_config_inputs,
            s3_asset_config_inputs=s3_asset_config_inputs,
        )

        template = assertions.Template.from_stack(cms_config_stack)
        assert template.to_json() == snapshot_json_with_matcher
