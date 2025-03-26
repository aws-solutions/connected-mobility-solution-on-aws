# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
import pytest
from syrupy.types import SerializableData

# AWS Libraries
from aws_cdk.assertions import Template


@pytest.mark.skip(reason="Hash in resources changes stochastically leading to failure.")
def test_cms_ui_snapshot(
    cms_ui_stack_template: Template,
    snapshot_json_with_matcher: SerializableData,
) -> None:
    assert cms_ui_stack_template.to_json() == snapshot_json_with_matcher
