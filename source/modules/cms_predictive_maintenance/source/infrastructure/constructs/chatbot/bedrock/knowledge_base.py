# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# AWS Libraries
from aws_cdk import ArnFormat, Stack, aws_bedrock, aws_iam
from constructs import Construct

# CMS Common Library
from cms_common.config.resource_names import ResourceName, ResourcePrefix
from cms_common.config.stack_inputs import SolutionConfigInputs

# Connected Mobility Solution on AWS
from ..interface import VectorIndexConfig
from .role import BedrockRoleConstruct


class BedrockKnowledgeBaseConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_unique_id: str,
        solution_config_inputs: SolutionConfigInputs,
        bedrock_role_construct: BedrockRoleConstruct,
        embedding_model_name: str,
        aoss_collection_id: str,
        vector_index_config: VectorIndexConfig,
    ) -> None:
        super().__init__(scope, construct_id)

        embedding_model_arn = Stack.of(self).format_arn(
            service="bedrock",
            resource="foundation-model",
            resource_name=embedding_model_name,
            arn_format=ArnFormat.SLASH_RESOURCE_NAME,
            account="",
        )

        bedrock_policy = aws_iam.Policy(
            self,
            "bedrock-policy",
            statements=[
                aws_iam.PolicyStatement(
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "aoss:APIAccessAll",
                    ],
                    resources=[
                        Stack.of(self).format_arn(
                            service="aoss",
                            resource="collection",
                            resource_name=aoss_collection_id,
                            arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                        )
                    ],
                ),
                aws_iam.PolicyStatement(
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "sts:AssumeRole",
                    ],
                    resources=["*"],  # NOSONAR
                    conditions={
                        "StringEquals": {
                            "aws:SourceAccount": Stack.of(self).account,
                        },
                        "ArnLike": {
                            "aws:SourceArn": f"arn:aws:bedrock:{Stack.of(self).region}:{Stack.of(self).account}:knowledge-base/*"
                        },
                    },
                ),
                aws_iam.PolicyStatement(
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "bedrock:InvokeModel",
                    ],
                    resources=[embedding_model_arn],
                ),
            ],
        )
        bedrock_role_construct.attach_policy_to_role(bedrock_policy)

        knowledge_base_name = ResourceName.hyphen_separated(
            prefix=ResourcePrefix.hyphen_separated(
                app_unique_id=app_unique_id,
                module_name=solution_config_inputs.module_short_name,
            ),
            name="knowledge-base",
        )

        self.knowledge_base = aws_bedrock.CfnKnowledgeBase(
            self,
            "knowledge-base",
            knowledge_base_configuration=aws_bedrock.CfnKnowledgeBase.KnowledgeBaseConfigurationProperty(
                type="VECTOR",
                vector_knowledge_base_configuration=aws_bedrock.CfnKnowledgeBase.VectorKnowledgeBaseConfigurationProperty(
                    embedding_model_arn=embedding_model_arn,
                ),
            ),
            name=knowledge_base_name,
            role_arn=bedrock_role_construct.role.role_arn,
            storage_configuration=aws_bedrock.CfnKnowledgeBase.StorageConfigurationProperty(
                type="OPENSEARCH_SERVERLESS",
                opensearch_serverless_configuration=aws_bedrock.CfnKnowledgeBase.OpenSearchServerlessConfigurationProperty(
                    collection_arn=Stack.of(self).format_arn(
                        service="aoss",
                        resource="collection",
                        resource_name=aoss_collection_id,
                        arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                    ),
                    field_mapping=aws_bedrock.CfnKnowledgeBase.OpenSearchServerlessFieldMappingProperty(
                        metadata_field=vector_index_config.vector.metadata_field,
                        text_field=vector_index_config.vector.text_field,
                        vector_field=vector_index_config.vector.name,
                    ),
                    vector_index_name=vector_index_config.name,
                ),
            ),
        )
        self.knowledge_base.node.add_dependency(bedrock_policy)
