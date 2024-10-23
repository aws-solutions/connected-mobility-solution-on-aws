# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json
from typing import List

# AWS Libraries
from aws_cdk import aws_opensearchserverless
from constructs import Construct


class VectorDBDataAccessConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        aoss_collection_name: str,
        role_arns: List[str],
    ) -> None:
        super().__init__(scope, construct_id)

        aoss_data_access_policy = [
            {
                "Rules": [
                    {
                        "Resource": [f"collection/{aoss_collection_name}"],
                        "Permission": [
                            "aoss:DescribeCollectionItems",
                            "aoss:CreateCollectionItems",
                            "aoss:UpdateCollectionItems",
                        ],
                        "ResourceType": "collection",
                    },
                    {
                        "Resource": [f"index/{aoss_collection_name}/*"],
                        "Permission": [
                            "aoss:UpdateIndex",
                            "aoss:DescribeIndex",
                            "aoss:ReadDocument",
                            "aoss:WriteDocument",
                            "aoss:CreateIndex",
                            "aoss:DeleteIndex",
                        ],
                        "ResourceType": "index",
                    },
                ],
                "Principal": role_arns,
                "Description": "data access policy for opensearch collection",
            }
        ]

        self.policy = aws_opensearchserverless.CfnAccessPolicy(
            self,
            "aoss-collection-data-access-policy",
            name=aoss_collection_name,
            policy=json.dumps(aoss_data_access_policy),
            type="data",
            description=f"{aoss_collection_name} - data access policy",
        )
