# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
from aws_cdk.assertions import Template
from syrupy.types import SerializableData


def test_cms_api_on_aws_snapshot(
    cms_api_on_aws_stack: Template, snapshot_json_with_matcher: SerializableData
) -> None:
    assert cms_api_on_aws_stack.to_json() == snapshot_json_with_matcher
