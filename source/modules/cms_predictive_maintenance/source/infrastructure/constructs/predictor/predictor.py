# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# AWS Libraries
from aws_cdk import aws_lambda
from constructs import Construct

# CMS Common Library
from cms_common.config.stack_inputs import SolutionConfigInputs
from cms_common.constructs.cmk_encrypted_s3 import CMKEncryptedS3Construct
from cms_common.constructs.custom_resource_lambda import CustomResourceLambdaConstruct
from cms_common.constructs.vpc_construct import VpcConstruct

# Connected Mobility Solution on AWS
from .interface import PredictorConstructOutputs
from .sagemaker.pipeline import PipelineAssetsS3Config, SageMakerPipelineConstruct
from .sagemaker.studio import SageMakerStudioConstruct


class PredictorConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_unique_id: str,
        vpc_construct: VpcConstruct,
        solution_config_inputs: SolutionConfigInputs,
        dependency_layer: aws_lambda.LayerVersion,
        custom_resource_lambda_construct: CustomResourceLambdaConstruct,
        sagemaker_assets_bucket_construct: CMKEncryptedS3Construct,
    ) -> None:
        super().__init__(scope, construct_id)

        SageMakerStudioConstruct(
            self,
            "sagemaker-studio",
            app_unique_id=app_unique_id,
            vpc_construct=vpc_construct,
            solution_config_inputs=solution_config_inputs,
            custom_resource_lambda_construct=custom_resource_lambda_construct,
        )

        pipeline_construct = SageMakerPipelineConstruct(
            self,
            "sagemaker-pipeline",
            app_unique_id=app_unique_id,
            solution_config_inputs=solution_config_inputs,
            custom_resource_lambda_construct=custom_resource_lambda_construct,
            pipeline_assets_s3_config=PipelineAssetsS3Config(
                bucket_name=sagemaker_assets_bucket_construct.bucket.bucket_name,
                kms_key_arn=sagemaker_assets_bucket_construct.key.key_arn,
                pipeline_definition_object_key="pipelines/predictive-maintenance-pipeline.json",
            ),
            vpc_construct=vpc_construct,
            dependency_layer=dependency_layer,
        )

        self.outputs = PredictorConstructOutputs(
            pipeline_role_arn=pipeline_construct.role.role_arn,
            pipeline_assets_bucket_name=sagemaker_assets_bucket_construct.bucket.bucket_name,
            deploy_model_lambda_function_arn=pipeline_construct.deploy_pipeline_model_function.function_arn,
            deploy_model_endpoint_name=pipeline_construct.deploy_model_endpoint_name,
        )
