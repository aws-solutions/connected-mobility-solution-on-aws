# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from datetime import datetime, timezone
from typing import Any, Dict
from unittest.mock import MagicMock

# AWS Libraries
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.stub import Stubber

# Connected Mobility Solution on AWS
from ..main import handler


def test_handler_create_endpoint(
    deploy_pipeline_model_event: Dict[str, Any],
    context: LambdaContext,
    mock_datetime: Any,
    mock_boto3_client: MagicMock,
    sagemaker_client_stubber: Stubber,
    deploy_pipeline_model_setup: Any,
) -> None:
    current_time = mock_datetime.FIXED_DATETIME.strftime("%Y-%m-%d-%H-%M")
    model_name = f"{current_time}-{deploy_pipeline_model_event['ResourceNameSuffix']}"
    endpoint_config_name = (
        f"{current_time}-{deploy_pipeline_model_event['ResourceNameSuffix']}"
    )

    sagemaker_client_stubber.add_response(
        "list_model_packages",
        {
            "ModelPackageSummaryList": [
                {
                    "ModelPackageArn": "arn:aws:sagemaker:us-west-2:123456789012:model-package/test-model-package",
                    "ModelPackageGroupName": "test-group",
                    "ModelPackageVersion": 1,
                    "ModelPackageStatus": "Completed",
                    "ModelApprovalStatus": "Approved",
                    "CreationTime": datetime(2023, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
                }
            ]
        },
        {
            "ModelPackageGroupName": deploy_pipeline_model_event[
                "ModelPackageGroupName"
            ],
            "ModelApprovalStatus": "Approved",
            "SortBy": "CreationTime",
            "SortOrder": "Descending",
            "MaxResults": 10,
        },
    )

    sagemaker_client_stubber.add_response(
        "create_model",
        {"ModelArn": "arn:aws:sagemaker:us-west-2:123456789012:model/test-model"},
        {
            "ModelName": model_name,
            "PrimaryContainer": {
                "ModelPackageName": "arn:aws:sagemaker:us-west-2:123456789012:model-package/test-model-package"
            },
            "ExecutionRoleArn": deploy_pipeline_model_event["PipelineExecutionRoleArn"],
        },
    )

    sagemaker_client_stubber.add_response(
        "create_endpoint_config",
        {
            "EndpointConfigArn": "arn:aws:sagemaker:us-west-2:123456789012:endpoint-config/test-endpoint-config"
        },
        {
            "EndpointConfigName": endpoint_config_name,
            "ProductionVariants": [
                {
                    "VariantName": "AllTraffic",
                    "ModelName": model_name,
                    "InstanceType": deploy_pipeline_model_event[
                        "InferenceInstanceType"
                    ],
                    "InitialInstanceCount": deploy_pipeline_model_event[
                        "InferenceInstanceCount"
                    ],
                }
            ],
        },
    )

    sagemaker_client_stubber.add_response(
        "create_endpoint",
        {
            "EndpointArn": "arn:aws:sagemaker:us-west-2:123456789012:endpoint/test-endpoint"
        },
        {
            "EndpointName": deploy_pipeline_model_event["EndpointName"],
            "EndpointConfigName": endpoint_config_name,
        },
    )

    mock_boto3_client("sagemaker", return_value=sagemaker_client_stubber.client)

    result = handler(deploy_pipeline_model_event, context)

    assert not result
    sagemaker_client_stubber.assert_no_pending_responses()


def test_handler_update_endpoint(
    deploy_pipeline_model_event: Dict[str, Any],
    context: LambdaContext,
    mock_datetime: Any,
    mock_boto3_client: MagicMock,
    sagemaker_client_stubber: Stubber,
    deploy_pipeline_model_setup: Any,
) -> None:
    current_time = mock_datetime.FIXED_DATETIME.strftime("%Y-%m-%d-%H-%M")
    model_name = f"{current_time}-{deploy_pipeline_model_event['ResourceNameSuffix']}"
    endpoint_config_name = (
        f"{current_time}-{deploy_pipeline_model_event['ResourceNameSuffix']}"
    )

    sagemaker_client_stubber.add_response(
        "list_model_packages",
        {
            "ModelPackageSummaryList": [
                {
                    "ModelPackageArn": "arn:aws:sagemaker:us-west-2:123456789012:model-package/test-model-package",
                    "ModelPackageGroupName": "test-group",
                    "ModelPackageVersion": 1,
                    "ModelPackageStatus": "Completed",
                    "ModelApprovalStatus": "Approved",
                    "CreationTime": datetime(2023, 1, 1, 10, 0, 0, tzinfo=timezone.utc),
                }
            ]
        },
        {
            "ModelPackageGroupName": deploy_pipeline_model_event[
                "ModelPackageGroupName"
            ],
            "ModelApprovalStatus": "Approved",
            "SortBy": "CreationTime",
            "SortOrder": "Descending",
            "MaxResults": 10,
        },
    )

    sagemaker_client_stubber.add_response(
        "create_model",
        {"ModelArn": "arn:aws:sagemaker:us-west-2:123456789012:model/test-model"},
        {
            "ModelName": model_name,
            "PrimaryContainer": {
                "ModelPackageName": "arn:aws:sagemaker:us-west-2:123456789012:model-package/test-model-package"
            },
            "ExecutionRoleArn": deploy_pipeline_model_event["PipelineExecutionRoleArn"],
        },
    )

    sagemaker_client_stubber.add_response(
        "create_endpoint_config",
        {
            "EndpointConfigArn": "arn:aws:sagemaker:us-west-2:123456789012:endpoint-config/test-endpoint-config"
        },
        {
            "EndpointConfigName": endpoint_config_name,
            "ProductionVariants": [
                {
                    "VariantName": "AllTraffic",
                    "ModelName": model_name,
                    "InstanceType": deploy_pipeline_model_event[
                        "InferenceInstanceType"
                    ],
                    "InitialInstanceCount": deploy_pipeline_model_event[
                        "InferenceInstanceCount"
                    ],
                }
            ],
        },
    )

    sagemaker_client_stubber.add_client_error(
        "create_endpoint", "ResourceInUse", "Endpoint already exists"
    )

    sagemaker_client_stubber.add_response(
        "update_endpoint",
        {
            "EndpointArn": "arn:aws:sagemaker:us-west-2:123456789012:endpoint/test-endpoint"
        },
        {
            "EndpointName": deploy_pipeline_model_event["EndpointName"],
            "EndpointConfigName": endpoint_config_name,
        },
    )

    mock_boto3_client("sagemaker", return_value=sagemaker_client_stubber.client)

    result = handler(deploy_pipeline_model_event, context)

    assert not result
    sagemaker_client_stubber.assert_no_pending_responses()
