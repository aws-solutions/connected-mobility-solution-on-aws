# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library

# Third Party Libraries
from aws_cdk import assertions

# Connected Mobility Solution on AWS
from ....infrastructure.stacks.common_dependencies_stack import CommonDependenciesStack


def test_layer_version_count(
    common_dependencies_stack: CommonDependenciesStack,
) -> None:
    template = assertions.Template.from_stack(common_dependencies_stack)
    template.resource_count_is("AWS::Lambda::LayerVersion", 1)
