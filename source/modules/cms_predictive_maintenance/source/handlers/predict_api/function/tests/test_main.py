# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import io
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, Generator
from unittest.mock import MagicMock

# Third Party Libraries
import pytest

# AWS Libraries
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.response import StreamingBody
from botocore.stub import Stubber

# Connected Mobility Solution on AWS
from ..main import handler


def str_to_streaming_body(input_str: str) -> StreamingBody:
    content_bytes = input_str.encode("utf-8")
    streaming_object = io.BytesIO(content_bytes)
    streaming_body = StreamingBody(streaming_object, len(content_bytes))
    return streaming_body


def test_predict_post_success(
    predict_post_event: Dict[str, Any],
    context: LambdaContext,
    mock_boto3_client: MagicMock,
    sagemaker_runtime_client_stubber: Stubber,
    predict_api_setup: Any,
    predict_api_env_vars: Generator[None, Any, Any],
) -> None:
    expected_prediction = "0.5,0.5"
    sagemaker_runtime_client_stubber.add_response(
        "invoke_endpoint",
        {
            "Body": str_to_streaming_body(input_str=expected_prediction),
            "ContentType": "text/csv",
            "InvokedProductionVariant": "AllTraffic",
            "CustomAttributes": "",
        },
        {
            "EndpointName": os.environ["SAGEMAKER_MODEL_ENDPOINT_NAME"],
            "Body": bytes(
                json.loads(predict_post_event["body"])["input"], encoding="utf-8"
            ),
            "ContentType": "text/csv",
        },
    )

    mock_boto3_client(
        "sagemaker-runtime", return_value=sagemaker_runtime_client_stubber.client
    )

    result = handler(predict_post_event, context)

    assert result["statusCode"] == 200
    assert result["body"] == json.dumps({"prediction": expected_prediction})
    sagemaker_runtime_client_stubber.assert_no_pending_responses()


def test_predict_post_fails_with_501(
    predict_post_event: Dict[str, Any],
    context: LambdaContext,
    predict_api_setup: Any,
    predict_api_env_vars: Generator[None, Any, Any],
) -> None:
    del os.environ["SAGEMAKER_MODEL_ENDPOINT_NAME"]
    result = handler(predict_post_event, context)

    assert result["statusCode"] == 500
    assert result["body"] == json.dumps(
        {"message": "SageMaker model endpoint name could not be determined."}
    )


def test_batch_predict_post_success(
    batch_predict_post_event: Dict[str, Any],
    context: LambdaContext,
    mock_boto3_client: MagicMock,
    sagemaker_client_stubber: Stubber,
    predict_api_setup: Any,
    predict_api_env_vars: Generator[None, Any, Any],
    mock_datetime: Any,
) -> None:
    inference_data_bucket_name = os.environ["BATCH_INFERENCE_DATA_S3_BUCKET_NAME"]
    inference_data_bucket_kms_key_id = os.environ[
        "BATCH_INFERENCE_DATA_S3_BUCKET_KMS_KEY_ID"
    ]
    input_data_s3_uri = f"s3://{inference_data_bucket_name}/{json.loads(batch_predict_post_event['body'])['input_data_s3_key']}"
    output_data_s3_key_prefix = os.environ["BATCH_INFERENCE_DATA_OUTPUT_S3_KEY_PREFIX"]
    output_data_s3_uri = (
        f"s3://{inference_data_bucket_name}/{output_data_s3_key_prefix}"
    )

    current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H-%M")
    transform_job_name = f"{current_time}-{os.environ['RESOURCE_NAME_SUFFIX']}"
    inference_instance_type = os.environ["BATCH_INFERENCE_INSTANCE_TYPE"]
    inference_instance_count = int(os.environ["BATCH_INFERENCE_INSTANCE_COUNT"])
    model_name = "test-cms-predictive-maintenance"

    sagemaker_client_stubber.add_response(
        "list_models",
        {
            "Models": [
                {
                    "ModelName": model_name,
                    "ModelArn": f"arn:aws:sagemaker:us-west-2:1234567890:model/{model_name}",
                    "CreationTime": datetime(2020, 1, 1),
                },
            ],
        },
        {
            "SortBy": "Name",
            "SortOrder": "Descending",
            "MaxResults": 10,
            "NameContains": os.environ["RESOURCE_NAME_SUFFIX"],
        },
    )

    sagemaker_client_stubber.add_response(
        "create_transform_job",
        {"TransformJobArn": "test-transform-job-arn"},
        {
            "TransformJobName": transform_job_name,
            "ModelName": model_name,
            "BatchStrategy": "MultiRecord",
            "TransformInput": {
                "DataSource": {
                    "S3DataSource": {
                        "S3DataType": "S3Prefix",
                        "S3Uri": input_data_s3_uri,
                    }
                },
                "ContentType": "text/csv",
                "CompressionType": "None",
                "SplitType": "Line",
            },
            "TransformOutput": {
                "S3OutputPath": output_data_s3_uri,
                "Accept": "text/csv",
                "AssembleWith": "Line",
                "KmsKeyId": inference_data_bucket_kms_key_id,
            },
            "TransformResources": {
                "InstanceType": inference_instance_type,
                "InstanceCount": inference_instance_count,
            },
            "DataProcessing": {
                "InputFilter": "$[1:]",
                "OutputFilter": "$",
                "JoinSource": "None",
            },
        },
    )
    mock_boto3_client("sagemaker", return_value=sagemaker_client_stubber.client)

    result = handler(batch_predict_post_event, context)

    assert result["statusCode"] == 200
    assert result["body"] == json.dumps({"transform-job-name": transform_job_name})
    sagemaker_client_stubber.assert_no_pending_responses()


@pytest.mark.parametrize(
    "env_var_name",
    [
        "RESOURCE_NAME_SUFFIX",
        "BATCH_INFERENCE_DATA_S3_BUCKET_NAME",
        "BATCH_INFERENCE_DATA_S3_BUCKET_KMS_KEY_ID",
        "BATCH_INFERENCE_DATA_OUTPUT_S3_KEY_PREFIX",
        "BATCH_INFERENCE_INSTANCE_TYPE",
        "BATCH_INFERENCE_INSTANCE_COUNT",
    ],
)
def test_batch_predict_post_fails_with_501(
    batch_predict_post_event: Dict[str, Any],
    context: LambdaContext,
    env_var_name: str,
    predict_api_setup: Any,
    predict_api_env_vars: Generator[None, Any, Any],
) -> None:
    del os.environ[env_var_name]
    result = handler(batch_predict_post_event, context)

    assert result["statusCode"] == 500
    assert result["body"] == json.dumps(
        {"message": "Internal server error determining configuration options."}
    )
