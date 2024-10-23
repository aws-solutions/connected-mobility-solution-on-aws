# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json

# AWS Libraries
from aws_cdk import ArnFormat, CustomResource, Stack, aws_iam, aws_opensearchserverless
from constructs import Construct

# CMS Common Library
from cms_common.constructs.custom_resource_lambda import CustomResourceLambdaConstruct

# Connected Mobility Solution on AWS
from .....handlers.custom_resource.function.lib.custom_resource_type_enum import (
    CustomResourceFunctionType,
)
from ..interface import VectorIndexConfig


class VectorDBIndexConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        custom_resource_lambda_construct: CustomResourceLambdaConstruct,
        aoss_collection_id: str,
        vector_index_config: VectorIndexConfig,
        aoss_data_access_policy: aws_opensearchserverless.CfnAccessPolicy,
    ) -> None:
        super().__init__(scope, construct_id)

        custom_resource_policy = aws_iam.Policy(
            self,
            "custom-resource-policy",
            statements=[
                aws_iam.PolicyStatement(
                    actions=[
                        "aoss:APIAccessAll",
                    ],
                    effect=aws_iam.Effect.ALLOW,
                    resources=[
                        Stack.of(self).format_arn(
                            service="aoss",
                            resource="collection",
                            resource_name=aoss_collection_id,
                            arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                        ),
                    ],
                ),
            ],
        )
        custom_resource_lambda_construct.add_policy_to_custom_resource_lambda(
            policy=custom_resource_policy,
        )

        vector_index_config_json = {
            "settings": {"index.knn": "true"},
            "mappings": {
                "properties": {
                    vector_index_config.vector.name: {
                        "type": vector_index_config.vector.vector_type,
                        "dimension": vector_index_config.vector.dimension,
                        "method": {
                            "name": vector_index_config.vector.method.name,
                            "space_type": vector_index_config.vector.method.space_type,
                            "engine": vector_index_config.vector.method.engine,
                            "parameters": {
                                "ef_construction": vector_index_config.vector.method.ef_construction,
                                "m": vector_index_config.vector.method.m,
                            },
                        },
                    },
                    vector_index_config.vector.metadata_field: {"type": "text"},
                    vector_index_config.vector.text_field: {"type": "text"},
                }
            },
        }
        manage_vector_index_custom_resource = CustomResource(
            self,
            "manage-aoss-vector-index-custom-resource",
            service_token=custom_resource_lambda_construct.function.function_arn,
            resource_type=f"Custom::{CustomResourceFunctionType.MANAGE_AOSS_VECTOR_INDEX.value}",
            properties={
                "Resource": CustomResourceFunctionType.MANAGE_AOSS_VECTOR_INDEX.value,
                "VectorIndexConfigJsonStr": json.dumps(vector_index_config_json),
                "VectorIndexName": vector_index_config.name,
                "AOSSCollectionId": aoss_collection_id,
            },
        )
        manage_vector_index_custom_resource.node.add_dependency(custom_resource_policy)
        manage_vector_index_custom_resource.node.add_dependency(aoss_data_access_policy)
