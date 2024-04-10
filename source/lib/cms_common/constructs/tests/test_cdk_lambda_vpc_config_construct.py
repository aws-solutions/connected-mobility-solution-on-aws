# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library

# Third Party Libraries
from syrupy.types import SerializableData

# AWS Libraries
from aws_cdk import assertions


def test_cdk_lambda_vpc_config_construct(
    cdk_lambda_vpc_config_construct_stack_template: assertions.Template,
    snapshot_json_with_matcher: SerializableData,
) -> None:
    assert (
        cdk_lambda_vpc_config_construct_stack_template.to_json()
        == snapshot_json_with_matcher
    )
