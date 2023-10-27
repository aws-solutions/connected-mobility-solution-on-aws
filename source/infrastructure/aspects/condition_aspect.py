# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library

# Standard Library
from typing import cast

# Third Party Libraries
import jsii
from aws_cdk import CfnCondition, CfnResource, IAspect
from constructs import IConstruct


@jsii.implements(IAspect)
class ConditionAspect:
    def __init__(self, condition: CfnCondition) -> None:
        self.condition = condition

    # Visits every resource defined in the construct and applies the specified condition to the applicable resources.
    def visit(self, node: IConstruct) -> None:
        resource: CfnResource = cast(CfnResource, node)
        if hasattr(resource, "cfn_options") and resource.cfn_options is not None:
            resource.cfn_options.condition = self.condition
