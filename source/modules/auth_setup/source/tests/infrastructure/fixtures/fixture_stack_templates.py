# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import tempfile
from typing import Any, Dict
from unittest.mock import MagicMock

# Third Party Libraries
import pytest
from syrupy.extensions.json import JSONSnapshotExtension
from syrupy.matchers import path_type
from syrupy.types import SerializableData

# AWS Libraries
from aws_cdk import Stack, assertions, aws_lambda

# CMS Common Library
from cms_common.config.stack_inputs import S3AssetConfigInputs

# Connected Mobility Solution on AWS
from ....infrastructure.auth_setup_stack import AuthSetupStack


@pytest.fixture(name="snapshot_json_with_matcher")
def fixture_snapshot_json_with_matcher(snapshot: SerializableData) -> SerializableData:
    matcher = path_type(
        mapping={"^(.*)\\.S3Key$": (str,), "^(.*)\\.TemplateURL\\.(.*)$": (list,)},
        regex=True,
    )
    return snapshot.use_extension(JSONSnapshotExtension)(matcher=matcher)


@pytest.fixture(name="auth_setup_stack_template", scope="session")
def fixture_auth_setup_stack_template() -> assertions.Template:
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
        stack = AuthSetupStack(
            app, "auth-setup", s3_asset_config_inputs=s3_asset_config_inputs
        )
        return assertions.Template.from_stack(stack=stack)


@pytest.fixture(name="auth_setup_stack_parameters", scope="session")
def fixture_auth_setup_stack_parameters(
    auth_setup_stack_template: assertions.Template,
) -> Dict[str, Any]:
    return dict(auth_setup_stack_template.to_json()["Parameters"])
