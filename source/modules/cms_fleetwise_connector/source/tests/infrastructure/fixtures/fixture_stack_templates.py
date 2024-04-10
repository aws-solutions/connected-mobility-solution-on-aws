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
import aws_cdk
from aws_cdk import aws_lambda

# CMS Common Library
from cms_common.config.stack_inputs import S3AssetConfigInputs, SolutionConfigInputs

# Connected Mobility Solution on AWS
from ....infrastructure.cms_fleetwise_connector_stack import CmsFleetWiseConnectorStack


@pytest.fixture(name="snapshot_json_with_matcher")
def fixture_snapshot_json_with_matcher(snapshot: SerializableData) -> SerializableData:
    matcher = path_type(
        mapping={
            "^(.*)\\.S3Key$": (str,),
            "^(.*)\\.TemplateURL\\.(.*)$": (list,),
            "^(.*)\\.Definition$": (str,),
        },
        regex=True,
    )
    return snapshot.use_extension(JSONSnapshotExtension)(matcher=matcher)


@pytest.fixture(name="cms_fleetwise_connector_stack_template", scope="session")
def fixture_cms_fleetwise_connector_stack_template() -> aws_cdk.assertions.Template:
    solution_config_inputs = SolutionConfigInputs(
        solution_name="solution",
        solution_id="id",
        solution_version="v0.0.0",
        application_type="solution",
        module_name="module",
        module_short_name="module",
        capability_id="CMS.XX",
    )

    s3_asset_config = S3AssetConfigInputs(
        bucket_base_name="bucketName",
        object_key_prefix="keyPrefix/",
    )

    with tempfile.TemporaryDirectory() as tmp_dir_name:
        # mock lambda code asset path
        aws_lambda.Code.from_asset = MagicMock(  # type: ignore[method-assign]
            return_value=aws_lambda.AssetCode(path=tmp_dir_name)
        )

        app = aws_cdk.App()
        stack = CmsFleetWiseConnectorStack(
            app,
            "cms-fleetwise-connector",
            s3_asset_config_inputs=s3_asset_config,
            solution_config_inputs=solution_config_inputs,
        )
        template = aws_cdk.assertions.Template.from_stack(stack)

        return template
