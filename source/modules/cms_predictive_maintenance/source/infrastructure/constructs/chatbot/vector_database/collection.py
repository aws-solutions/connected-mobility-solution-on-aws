# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# AWS Libraries
from aws_cdk import aws_opensearchserverless
from constructs import Construct


class VectorDBCollectionConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        aoss_collection_name: str,
    ) -> None:
        super().__init__(scope, construct_id)

        self.collection = aws_opensearchserverless.CfnCollection(
            self,
            "aoss-collection",
            name=aoss_collection_name,
            description=f"{aoss_collection_name} - collection",
            type="VECTORSEARCH",
        )
