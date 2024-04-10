# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any

# AWS Libraries
from aws_cdk import App, Aspects, CfnCondition, Stack, assertions, aws_kms
from constructs import Construct

# Connected Mobility Solution on AWS
from ..condition import ConditionAspect


class AspectTestStack(Stack):
    def __init__(
        self, scope: Construct, construct_id: str, add_condition: bool, **kwargs: Any
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.test_key = aws_kms.Key(
            self,
            "test-key",
            enable_key_rotation=True,
        )
        cfn_condition = CfnCondition(
            self,
            "test-condition",
        )
        if add_condition:
            Aspects.of(self.test_key).add(ConditionAspect(cfn_condition))


def test_condition_aspect_true() -> None:
    app = App()
    test_stack = AspectTestStack(app, "condition-test-stack", add_condition=True)

    template = assertions.Template.from_stack(test_stack)
    template.has_resource("AWS::KMS::Key", {"Condition": "testcondition"})


def test_condition_aspect_false() -> None:
    app = App()
    test_stack = AspectTestStack(app, "condition-test-stack", add_condition=False)

    template = assertions.Template.from_stack(test_stack)
    template.has_resource("AWS::KMS::Key", {"Condition": None})
