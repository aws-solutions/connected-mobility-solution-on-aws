# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library

# Third Party Libraries
from aws_cdk import Stack, assertions


def test_layer_version_count(
    lambda_dependencies_stack: Stack,
) -> None:
    template = assertions.Template.from_stack(lambda_dependencies_stack)
    template.resource_count_is("AWS::Lambda::LayerVersion", 1)
