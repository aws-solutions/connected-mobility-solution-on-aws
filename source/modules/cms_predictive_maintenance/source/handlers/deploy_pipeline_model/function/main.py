# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import datetime
import os
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Dict

# AWS Libraries
import boto3
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.config import Config

if TYPE_CHECKING:
    # Third Party Libraries
    from mypy_boto3_sagemaker import SageMakerClient
else:
    SageMakerClient = object

tracer = Tracer()
logger = Logger()


@lru_cache(maxsize=1)
def get_sagemaker_client() -> SageMakerClient:
    return boto3.client(
        "sagemaker", config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"])
    )


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: Dict[str, Any], context: LambdaContext) -> Dict[Any, Any]:
    resource_name_suffix = event["ResourceNameSuffix"]
    current_time = datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%d-%H-%M"
    )

    endpoint_config_name = f"{current_time}-{resource_name_suffix}"
    model_name = f"{current_time}-{resource_name_suffix}"
    endpoint_name = event["EndpointName"]

    list_model_packages_response = get_sagemaker_client().list_model_packages(
        ModelPackageGroupName=event["ModelPackageGroupName"],
        ModelApprovalStatus="Approved",
        SortBy="CreationTime",
        SortOrder="Descending",
        MaxResults=10,
    )

    model_package_arn = list_model_packages_response["ModelPackageSummaryList"][0][
        "ModelPackageArn"
    ]

    get_sagemaker_client().create_model(
        ModelName=model_name,
        PrimaryContainer={"ModelPackageName": model_package_arn},
        ExecutionRoleArn=event["PipelineExecutionRoleArn"],
    )

    get_sagemaker_client().create_endpoint_config(
        EndpointConfigName=endpoint_config_name,
        ProductionVariants=[
            {
                "VariantName": "AllTraffic",
                "ModelName": model_name,
                "InstanceType": event["InferenceInstanceType"],
                "InitialInstanceCount": event["InferenceInstanceCount"],
            }
        ],
    )

    try:
        get_sagemaker_client().create_endpoint(
            EndpointName=endpoint_name,
            EndpointConfigName=endpoint_config_name,
        )
    except get_sagemaker_client().exceptions.ClientError:
        get_sagemaker_client().update_endpoint(
            EndpointName=endpoint_name,
            EndpointConfigName=endpoint_config_name,
        )

    return {}
