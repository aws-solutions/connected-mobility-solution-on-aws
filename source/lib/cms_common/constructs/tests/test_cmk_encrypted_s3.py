# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
from syrupy.types import SerializableData

# AWS Libraries
from aws_cdk import assertions


def test_cmk_encrypted_s3_snapshot(
    cmk_encrpyted_s3_stack: assertions.Template,
    snapshot_json_with_matcher: SerializableData,
) -> None:

    assert cmk_encrpyted_s3_stack.to_json() == snapshot_json_with_matcher
