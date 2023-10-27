# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0


# Standard Library
# pylint: disable=duplicate-code
from os.path import dirname, realpath
from typing import Any

# Third Party Libraries
from aws_cdk import App, Stack, assertions, aws_kms
from constructs import Construct

# Connected Mobility Solution on AWS
from ....infrastructure.aspects.nag_suppression import NagSuppression, NagType


class NagTestStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.test_key = aws_kms.Key(
            self,
            "nag-test-key",
            enable_key_rotation=True,
        )


def test_nag_suppression_cdk_metadata() -> None:
    app = App()
    test_stack = NagTestStack(app, "nag-test-stack")
    cdk_nag_suppression = NagSuppression(
        f"{dirname(realpath(__file__))}/test-cdk-nag-suppression-list.json",
        NagType.CDK_NAG,
    )
    l1_construct = test_stack.test_key.node.default_child
    if l1_construct is not None:
        cdk_nag_suppression.visit(l1_construct)
        template = assertions.Template.from_stack(test_stack)
        template.has_resource(
            "AWS::KMS::Key",
            {
                "Metadata": {
                    "cdk_nag": {
                        "rules_to_suppress": [
                            {"id": "test-cdk-id", "reason": "test-cdk-reason"}
                        ]
                    }
                }
            },
        )
    else:
        assert False


def test_nag_suppression_cfn_metadata() -> None:
    app = App()
    test_stack = NagTestStack(app, "nag-test-stack")
    cfn_nag_suppression = NagSuppression(
        f"{dirname(realpath(__file__))}/test-cfn-nag-suppression-list.json",
        NagType.CFN_NAG,
    )

    l1_construct = test_stack.test_key.node.default_child
    if l1_construct is not None:
        cfn_nag_suppression.visit(l1_construct)
        template = assertions.Template.from_stack(test_stack)
        template.has_resource(
            "AWS::KMS::Key",
            {
                "Metadata": {
                    "cfn_nag": {
                        "rules_to_suppress": [
                            {"id": "test-cfn-id", "reason": "test-cfn-reason"}
                        ]
                    }
                }
            },
        )
    else:
        assert False
