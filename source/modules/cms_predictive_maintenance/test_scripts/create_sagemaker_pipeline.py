# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
# Standard Library
import argparse
import uuid

# AWS Libraries
import boto3

# Connected Mobility Solution on AWS
from ..source.handlers.custom_resource.function.lib.pipeline import (
    create_predictive_maintenance_pipeline,
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--app-unique-id", type=str, default="cms")
    parser.add_argument("--pipeline-name", type=str, required=True)
    args = parser.parse_args()

    sagemaker = boto3.client("sagemaker")
    ssm_client = boto3.client("ssm")

    pipeline_role_arn = ssm_client.get_parameter(
        Name=f"/solution/{args.app_unique_id}/predictive-maintenance/predictor/pipeline/role-arn"
    )["Parameter"]["Value"]
    pipeline_assets_bucket_name = ssm_client.get_parameter(
        Name=f"/solution/{args.app_unique_id}/predictive-maintenance/predictor/pipeline/assets-bucket/name"
    )["Parameter"]["Value"]
    pipeline_deploy_model_lambda_function_arn = ssm_client.get_parameter(
        Name=f"/solution/{args.app_unique_id}/predictive-maintenance/predictor/pipeline/deploy-model-lambda/arn"
    )["Parameter"]["Value"]
    pipeline_deploy_model_endpoint_name = ssm_client.get_parameter(
        Name=f"/solution/{args.app_unique_id}/predictive-maintenance/predictor/pipeline/deploy-model-endpoint/name"
    )["Parameter"]["Value"]

    pipeline = create_predictive_maintenance_pipeline(
        pipeline_name=args.pipeline_name,
        pipeline_role_arn=pipeline_role_arn,
        pipeline_assets_bucket_name=pipeline_assets_bucket_name,
        deploy_model_function_arn=pipeline_deploy_model_lambda_function_arn,
        endpoint_name=pipeline_deploy_model_endpoint_name,
        resource_name_prefix=args.pipeline_name,
    )

    sagemaker.create_pipeline(
        PipelineName=args.pipeline_name,
        PipelineDefinition=pipeline.definition(),
        RoleArn=pipeline_role_arn,
        ClientRequestToken=str(uuid.uuid4()),
    )
