# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
# Standard Library
import os

# Third Party Libraries
import pytest
from syrupy.extensions.json import JSONSnapshotExtension
from syrupy.matchers import path_value
from syrupy.types import SerializableData

# AWS Libraries
import aws_cdk

# CMS Common Library
from cms_common.config.stack_inputs import S3AssetConfigInputs, SolutionConfigInputs

# Connected Mobility Solution on AWS
from ....infrastructure.acdp_backstage_stack import AcdpBackstageStack


@pytest.fixture(name="snapshot_json_with_matcher")
def fixture_snapshot_json_with_matcher(snapshot: SerializableData) -> SerializableData:
    matcher = path_value(
        mapping={
            ".*": r"(\/?([0-9a-fA-F]+)\.zip|[a-zA-Z0-9:/-]+([0-9]{12})[a-zA-Z0-9:/-]+)",
        },
        regex=True,
        types=(object,),
        replacer=lambda data, match: data.replace(match[1], "test") if match else data,
    )
    return snapshot.use_extension(JSONSnapshotExtension)(matcher=matcher)


@pytest.fixture(name="acdp_backstage_stack_template", scope="session")
def fixture_acdp_backstage_stack_template() -> aws_cdk.assertions.Template:
    os.environ["BACKSTAGE_IMAGE_TAG"] = "DUMMY"
    os.environ["S3_ASSET_KEY_PREFIX"] = "asset-test.zip"
    os.environ["USER_AGENT_STRING"] = "test-string"
    os.environ["ROUTE53_HOSTED_ZONE_ID"] = "Z0123456789ABCDE12PKU"
    os.environ["FULLY_QUALIFIED_DOMAIN_NAME"] = "dummy"
    os.environ["IS_PUBLIC_FACING"] = "true"

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

    app = aws_cdk.App()
    stack = AcdpBackstageStack(
        app,
        "backstage",
        env=aws_cdk.Environment(
            account="test-account-id",
            region="us-west-2",
        ),
        solution_config_inputs=solution_config_inputs,
        s3_asset_config_inputs=s3_asset_config_inputs,
        s3_asset_bucket_name="test-bucket-name",
    )
    template = aws_cdk.assertions.Template.from_stack(stack)
    return template
