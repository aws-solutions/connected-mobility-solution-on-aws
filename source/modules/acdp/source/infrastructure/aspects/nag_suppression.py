# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json
from enum import Enum

# Third Party Libraries
import jsii

# AWS Libraries
from aws_cdk import CfnResource, IAspect
from constructs import IConstruct


class NagType(Enum):
    CDK_NAG = "cdk_nag"
    CFN_NAG = "cfn_nag"


@jsii.implements(IAspect)
class NagSuppression:
    def __init__(self, suppression_file_path: str, nag_type: NagType) -> None:
        with open(suppression_file_path, encoding="UTF-8") as suppression_file:
            self.suppressions = dict(json.loads(suppression_file.read()))
            self.nag_type = nag_type

    # Visits every resource defined in cfn template and applies suppression metadata by resource path from the suppresions file provided
    # Resource paths in our suppression lists must be to L1 constructs. When visiting an L2 construct, the path will not match
    # and the resource will be skipped, however, the supporting L1 construct which eventually be visited, and the suppression will be added then
    def visit(self, node: IConstruct) -> None:
        node_path = f"/{node.node.path}"
        suppression_metadata = self.suppressions.get(node_path)

        if suppression_metadata:
            CfnResource.add_metadata(
                node, key=self.nag_type.value, value=suppression_metadata  # type: ignore
            )
