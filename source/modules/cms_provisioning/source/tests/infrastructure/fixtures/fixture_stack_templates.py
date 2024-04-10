# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import tempfile
from unittest.mock import MagicMock

# Third Party Libraries
import pytest
from syrupy.extensions.json import JSONSnapshotExtension
from syrupy.matchers import path_type
from syrupy.types import SerializableData

# AWS Libraries
from aws_cdk import Stack, assertions, aws_lambda

# CMS Common Library
from cms_common.config.stack_inputs import S3AssetConfigInputs, SolutionConfigInputs

# Connected Mobility Solution on AWS
from ....infrastructure.cms_provisioning_stack import CmsProvisioningStack


@pytest.fixture(name="snapshot_json_with_matcher")
def fixture_snapshot_json_with_matcher(snapshot: SerializableData) -> SerializableData:
    matcher = path_type(
        mapping={"^(.*)\\.S3Key$": (str,), "^(.*)\\.TemplateURL\\.(.*)$": (list,)},
        regex=True,
    )
    return snapshot.use_extension(JSONSnapshotExtension)(matcher=matcher)


@pytest.fixture(name="cms_provisioning_stack_template", scope="session")
def fixture_cms_provisioning_stack_template() -> assertions.Template:
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
    with tempfile.TemporaryDirectory() as tmpdirname:
        # mock lambda code asset path
        aws_lambda.Code.from_asset = MagicMock(  # type: ignore[method-assign]
            return_value=aws_lambda.AssetCode(path=tmpdirname)
        )
        app = Stack()
        stack = CmsProvisioningStack(
            app,
            "cms-provisioning-stack",
            solution_config_inputs=solution_config_inputs,
            s3_asset_config_inputs=s3_asset_config_inputs,
        )
        return assertions.Template.from_stack(stack=stack)
