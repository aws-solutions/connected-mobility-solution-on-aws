# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json
from enum import Enum

# Third Party Libraries
import jsii
from aws_cdk import CfnResource, IAspect
from constructs import IConstruct


class NagType(Enum):
    CDK_NAG = "cdk_nag"
    CFN_NAG = "cfn_nag"


@jsii.implements(IAspect)
class NagSuppression:
    def __init__(self, suppression_list_path: str, nag_type: NagType) -> None:
        with open(suppression_list_path, encoding="UTF-8") as suppression_file:
            self.suppressions = dict(json.loads(suppression_file.read()))
            self.nag_type = nag_type

    # Nag suppressions MUST be applied to the metadata of the L1 construct.
    # Although the higher construct will be visited by this Aspect, it will be silently skipped if the path is not defined as a key in the suppression json.
    def visit(self, node: IConstruct) -> None:
        node_path = f"/{node.node.path}"
        suppression_metadata = self.suppressions.get(node_path)
        if suppression_metadata:
            CfnResource.add_metadata(
                node, key=self.nag_type.value, value=suppression_metadata  # type: ignore
            )
