# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
from syrupy.types import SerializableData

# AWS Libraries
from aws_cdk.assertions import Template


def test_cms_api_snapshot(
    cms_api_stack_template: Template,
    snapshot_json_with_matcher: SerializableData,
) -> None:
    assert cms_api_stack_template.to_json() == snapshot_json_with_matcher
