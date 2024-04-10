# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
# Standard Library

# Third Party Libraries
from syrupy.types import SerializableData

# AWS Libraries
from aws_cdk import assertions


def test_identity_provider_config_snapshot(
    identity_provider_config_stack: assertions.Template,
    snapshot_json_with_matcher: SerializableData,
) -> None:
    assert identity_provider_config_stack.to_json() == snapshot_json_with_matcher
