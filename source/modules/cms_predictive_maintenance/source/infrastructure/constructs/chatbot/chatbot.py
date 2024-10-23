# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import List

# AWS Libraries
from aws_cdk import aws_bedrock
from constructs import Construct

# CMS Common Library
from cms_common.config.resource_names import ResourceName, ResourcePrefix
from cms_common.config.stack_inputs import SolutionConfigInputs
from cms_common.constructs.custom_resource_lambda import CustomResourceLambdaConstruct

# Connected Mobility Solution on AWS
from ..module_integration import ModuleInputsConstruct
from .bedrock.agent import BedrockAgentConstruct
from .bedrock.data_source import BedrockDataSourceConstruct
from .bedrock.knowledge_base import BedrockKnowledgeBaseConstruct
from .bedrock.role import BedrockRoleConstruct
from .interface import (
    AgentConfig,
    ChatbotConstructOutputs,
    DataSourceChunkingConfig,
    EmbeddingModelConfig,
    S3DataSourceConfig,
    VectorIndexConfig,
)
from .vector_database.collection import VectorDBCollectionConstruct
from .vector_database.data_access import VectorDBDataAccessConstruct
from .vector_database.index import VectorDBIndexConstruct
from .vector_database.security import VectorDBSecurityConstruct


class ChatbotConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        module_inputs_construct: ModuleInputsConstruct,
        solution_config_inputs: SolutionConfigInputs,
        custom_resource_lambda_construct: CustomResourceLambdaConstruct,
        embedding_model_inputs: EmbeddingModelConfig,
        s3_data_source_inputs: S3DataSourceConfig,
        data_source_chunking_config: DataSourceChunkingConfig,
        vector_index_config: VectorIndexConfig,
        agent_config: AgentConfig,
        agent_action_groups: List[aws_bedrock.CfnAgent.AgentActionGroupProperty],
    ) -> None:
        super().__init__(scope, construct_id)

        aoss_collection_name = ResourceName.hyphen_separated(
            prefix=ResourcePrefix.hyphen_separated(
                app_unique_id=module_inputs_construct.app_unique_id,
                module_name=solution_config_inputs.module_short_name,
            ),
            name="",
        )

        vector_db_security_construct = VectorDBSecurityConstruct(
            self,
            "vector-db-security-construct",
            custom_resource_lambda_construct=custom_resource_lambda_construct,
            aoss_collection_name=aoss_collection_name,
            vpc_config=module_inputs_construct.vpc_config,
        )

        vector_db_collection_construct = VectorDBCollectionConstruct(
            self,
            "vector-db-collection-construct",
            aoss_collection_name=aoss_collection_name,
        )
        vector_db_collection_construct.node.add_dependency(vector_db_security_construct)

        bedrock_role_construct = BedrockRoleConstruct(
            self,
            "bedrock-role-construct",
            app_unique_id=module_inputs_construct.app_unique_id,
        )

        vector_db_data_access_construct = VectorDBDataAccessConstruct(
            self,
            "vector-db-data-access-construct",
            aoss_collection_name=aoss_collection_name,
            role_arns=[
                custom_resource_lambda_construct.role.role_arn,
                bedrock_role_construct.role.role_arn,
            ],
        )

        vector_db_index_construct = VectorDBIndexConstruct(
            self,
            "vector-index-construct",
            custom_resource_lambda_construct=custom_resource_lambda_construct,
            aoss_collection_id=vector_db_collection_construct.collection.attr_id,
            vector_index_config=vector_index_config,
            aoss_data_access_policy=vector_db_data_access_construct.policy,
        )

        bedrock_knowledge_base_construct = BedrockKnowledgeBaseConstruct(
            self,
            "bedrock-knowledge-base-construct",
            app_unique_id=module_inputs_construct.app_unique_id,
            solution_config_inputs=solution_config_inputs,
            bedrock_role_construct=bedrock_role_construct,
            embedding_model_name=embedding_model_inputs.model_name,
            aoss_collection_id=vector_db_collection_construct.collection.attr_id,
            vector_index_config=vector_index_config,
        )
        bedrock_knowledge_base_construct.node.add_dependency(vector_db_index_construct)

        BedrockDataSourceConstruct(
            self,
            "bedrock-data-source-construct",
            app_unique_id=module_inputs_construct.app_unique_id,
            solution_config_inputs=solution_config_inputs,
            custom_resource_lambda_construct=custom_resource_lambda_construct,
            bedrock_role_construct=bedrock_role_construct,
            knowledge_base_id=bedrock_knowledge_base_construct.knowledge_base.attr_knowledge_base_id,
            data_source_inputs=s3_data_source_inputs,
            data_source_chunking_config=data_source_chunking_config,
        )

        bedrock_agent = BedrockAgentConstruct(
            self,
            "bedrock-agent-construct",
            app_unique_id=module_inputs_construct.app_unique_id,
            solution_config_inputs=solution_config_inputs,
            knowledge_base_id=bedrock_knowledge_base_construct.knowledge_base.attr_knowledge_base_id,
            agent_config=agent_config,
            action_groups=agent_action_groups,
        )

        self.outputs = ChatbotConstructOutputs(
            knowledge_base_id=bedrock_knowledge_base_construct.knowledge_base.attr_knowledge_base_id,
            agent_id=bedrock_agent.agent.attr_agent_id,
            agent_alias_id=bedrock_agent.agent_alias.attr_agent_alias_id,
        )
