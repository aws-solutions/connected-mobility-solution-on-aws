# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
# Standard Library

# AWS Libraries
from aws_cdk import ArnFormat, CustomResource, Stack, aws_bedrock, aws_iam
from constructs import Construct

# CMS Common Library
from cms_common.config.resource_names import ResourceName, ResourcePrefix
from cms_common.config.stack_inputs import SolutionConfigInputs
from cms_common.constructs.custom_resource_lambda import CustomResourceLambdaConstruct

# Connected Mobility Solution on AWS
from .....handlers.custom_resource.function.lib.custom_resource_type_enum import (
    CustomResourceFunctionType,
)
from ..interface import DataSourceChunkingConfig, S3DataSourceConfig
from .role import BedrockRoleConstruct


class BedrockDataSourceConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_unique_id: str,
        solution_config_inputs: SolutionConfigInputs,
        custom_resource_lambda_construct: CustomResourceLambdaConstruct,
        bedrock_role_construct: BedrockRoleConstruct,
        data_source_inputs: S3DataSourceConfig,
        data_source_chunking_config: DataSourceChunkingConfig,
        knowledge_base_id: str,
    ) -> None:
        super().__init__(scope, construct_id)

        custom_resource_policy = aws_iam.Policy(
            self,
            "custom-resource-policy",
            statements=[
                aws_iam.PolicyStatement(
                    actions=[
                        "bedrock:StartIngestionJob",
                    ],
                    effect=aws_iam.Effect.ALLOW,
                    resources=["*"],
                ),
            ],
        )
        custom_resource_lambda_construct.add_policy_to_custom_resource_lambda(
            policy=custom_resource_policy,
        )

        bedrock_policy = aws_iam.Policy(
            self,
            "bedrock-policy",
            document=aws_iam.PolicyDocument(
                statements=[
                    aws_iam.PolicyStatement(
                        effect=aws_iam.Effect.ALLOW,
                        actions=[
                            "s3:ListBucket",
                        ],
                        resources=[
                            Stack.of(self).format_arn(
                                service="s3",
                                resource=data_source_inputs.bucket_name,
                                resource_name=None,
                                account="",
                                region="",
                                arn_format=ArnFormat.NO_RESOURCE_NAME,
                            ),
                        ],
                        conditions={
                            "StringEquals": {
                                "aws:ResourceAccount": Stack.of(self).account,
                            }
                        },
                    ),
                    aws_iam.PolicyStatement(
                        effect=aws_iam.Effect.ALLOW,
                        actions=[
                            "s3:GetObject",
                        ],
                        resources=[
                            Stack.of(self).format_arn(
                                service="s3",
                                resource=data_source_inputs.bucket_name,
                                resource_name=f"{data_source_inputs.object_key_prefix}/*",
                                account="",
                                region="",
                                arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                            ),
                        ],
                        conditions={
                            "StringEquals": {
                                "aws:ResourceAccount": Stack.of(self).account,
                            }
                        },
                    ),
                ]
            ),
        )
        bedrock_role_construct.attach_policy_to_role(bedrock_policy)

        data_source_name = ResourceName.hyphen_separated(
            prefix=ResourcePrefix.hyphen_separated(
                app_unique_id=app_unique_id,
                module_name=solution_config_inputs.module_short_name,
            ),
            name="data-source",
        )

        self.data_source = aws_bedrock.CfnDataSource(
            self,
            "data-source",
            data_source_configuration=aws_bedrock.CfnDataSource.DataSourceConfigurationProperty(
                s3_configuration=aws_bedrock.CfnDataSource.S3DataSourceConfigurationProperty(
                    bucket_arn=Stack.of(self).format_arn(
                        service="s3",
                        resource=data_source_inputs.bucket_name,
                        resource_name=None,
                        account="",
                        region="",
                        arn_format=ArnFormat.NO_RESOURCE_NAME,
                    ),
                    bucket_owner_account_id=Stack.of(self).account,
                    inclusion_prefixes=[data_source_inputs.object_key_prefix],
                ),
                type="S3",
            ),
            knowledge_base_id=knowledge_base_id,
            name=data_source_name,
            vector_ingestion_configuration=aws_bedrock.CfnDataSource.VectorIngestionConfigurationProperty(
                chunking_configuration=aws_bedrock.CfnDataSource.ChunkingConfigurationProperty(
                    chunking_strategy=data_source_chunking_config.strategy,
                    fixed_size_chunking_configuration=aws_bedrock.CfnDataSource.FixedSizeChunkingConfigurationProperty(
                        max_tokens=data_source_chunking_config.max_tokens,
                        overlap_percentage=data_source_chunking_config.overlap_percentage,
                    ),
                )
            ),
        )

        ingest_bedrock_data_source_custom_resource = CustomResource(
            self,
            "ingest-bedrock-data-source-custom-resource",
            service_token=custom_resource_lambda_construct.function.function_arn,
            resource_type=f"Custom::{CustomResourceFunctionType.INGEST_BEDROCK_DATA_SOURCE.value}",
            properties={
                "Resource": CustomResourceFunctionType.INGEST_BEDROCK_DATA_SOURCE.value,
                "DataSourceId": self.data_source.attr_data_source_id,
                "KnowledgeBaseId": knowledge_base_id,
            },
        )
        ingest_bedrock_data_source_custom_resource.node.add_dependency(
            custom_resource_policy
        )
