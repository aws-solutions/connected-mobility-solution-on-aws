# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
import aws_cdk
import pytest
from syrupy.extensions.json import JSONSnapshotExtension
from syrupy.matchers import path_type
from syrupy.types import SerializableData

# Connected Mobility Solution on AWS
from ....infrastructure.cms_api_on_aws_stack import CmsAPIOnAwsStack


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


@pytest.fixture(name="cms_api_on_aws_stack", scope="session")
def fixture_cms_api_on_aws_stack() -> aws_cdk.assertions.Template:
    app = aws_cdk.App()
    stack = CmsAPIOnAwsStack(app, "cms-api-on-aws")
    template = aws_cdk.assertions.Template.from_stack(stack)
    return template
