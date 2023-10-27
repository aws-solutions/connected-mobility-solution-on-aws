# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from os.path import dirname, realpath

# Third Party Libraries
from aws_cdk import assertions

# Connected Mobility Solution on AWS
from ....infrastructure.aspects.nag_suppression import NagSuppression, NagType
from ..fixtures.fixture_stack import NagTestStack


def test_nag_suppression_metadata(test_stack: NagTestStack) -> None:
    cdk_nag_suppression = NagSuppression(
        f"{dirname(realpath(__file__))}/test_cdk_nag_suppression_list.json",
        NagType.CDK_NAG,
    )
    cfn_nag_suppression = NagSuppression(
        f"{dirname(realpath(__file__))}/test_cfn_nag_suppression_list.json",
        NagType.CFN_NAG,
    )
    l1_construct = test_stack.test_key.node.default_child
    if l1_construct is not None:
        cdk_nag_suppression.visit(l1_construct)
        cfn_nag_suppression.visit(l1_construct)
        template = assertions.Template.from_stack(test_stack)
        template.has_resource(
            "AWS::KMS::Key",
            {
                "Metadata": {
                    "cdk_nag": {
                        "rules_to_suppress": [
                            {"id": "test-cdk-id", "reason": "test-cdk-reason"}
                        ]
                    },
                    "cfn_nag": {
                        "rules_to_suppress": [
                            {"id": "test-cfn-id", "reason": "test-cfn-reason"}
                        ]
                    },
                }
            },
        )
    else:
        assert False
