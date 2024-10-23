# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json
import os
from datetime import datetime, timezone
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Callable, Dict

# AWS Libraries
import boto3
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.config import Config

if TYPE_CHECKING:
    # Third Party Libraries
    from mypy_boto3_sagemaker import SageMakerClient
    from mypy_boto3_sagemaker_runtime import SageMakerRuntimeClient
else:
    SageMakerRuntimeClient = object
    SageMakerClient = object

tracer = Tracer()
logger = Logger()


@lru_cache(maxsize=1)
def get_sagemaker_runtime_client() -> SageMakerRuntimeClient:
    return boto3.client(
        "sagemaker-runtime",
        config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"]),
    )


@lru_cache(maxsize=1)
def get_sagemaker_client() -> SageMakerClient:
    return boto3.client(
        "sagemaker",
        config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"]),
    )


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def get_prediction(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    response = {
        "statusCode": 400,
        "body": json.dumps({"message": "Unexpected error."}),
    }

    model_input = json.loads(event["body"])["input"]
    try:
        endpoint_name = os.environ["SAGEMAKER_MODEL_ENDPOINT_NAME"]
    except KeyError:
        response["statusCode"] = 500
        response["body"] = json.dumps(
            {"message": "SageMaker model endpoint name could not be determined."}
        )
        return response

    try:
        invoke_endpoint_response = get_sagemaker_runtime_client().invoke_endpoint(
            EndpointName=endpoint_name,
            Body=bytes(model_input, encoding="utf-8"),
            ContentType="text/csv",
        )
        response["statusCode"] = 200
        response["body"] = json.dumps(
            {"prediction": invoke_endpoint_response["Body"].read().decode("utf-8")}
        )
    except KeyError:
        response["statusCode"] = 400
        response["body"] = json.dumps(
            {"message": "No output received from invoking SageMaker model."}
        )
    except get_sagemaker_runtime_client().exceptions.ModelError:
        response["statusCode"] = 400
        response["body"] = json.dumps(
            {"message": "Invalid input to the SageMaker model."}
        )
    except get_sagemaker_runtime_client().exceptions.ValidationError:
        response["statusCode"] = 500
        response["body"] = json.dumps(
            {
                "message": "SageMaker model endpoint not found. Make sure the model was deployed."
            }
        )

    return response


def get_latest_deployable_model_name() -> str:
    model_name_suffix = os.environ["RESOURCE_NAME_SUFFIX"]
    list_models_response = get_sagemaker_client().list_models(
        SortBy="Name",
        SortOrder="Descending",
        MaxResults=10,
        NameContains=model_name_suffix,
    )
    return list_models_response["Models"][0]["ModelName"]


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def start_batch_prediction(
    event: Dict[str, Any], context: LambdaContext
) -> Dict[str, Any]:
    response = {
        "statusCode": 400,
        "body": json.dumps({"message": "Unexpected error."}),
    }

    request_body = json.loads(event["body"])

    try:
        inference_data_bucket_name = os.environ["BATCH_INFERENCE_DATA_S3_BUCKET_NAME"]
        inference_data_bucket_kms_key_id = os.environ[
            "BATCH_INFERENCE_DATA_S3_BUCKET_KMS_KEY_ID"
        ]
        input_data_s3_uri = (
            f"s3://{inference_data_bucket_name}/{request_body['input_data_s3_key']}"
        )
        output_data_s3_key_prefix = os.environ[
            "BATCH_INFERENCE_DATA_OUTPUT_S3_KEY_PREFIX"
        ]
        output_data_s3_uri = (
            f"s3://{inference_data_bucket_name}/{output_data_s3_key_prefix}"
        )

        current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H-%M")
        transform_job_name = f"{current_time}-{os.environ['RESOURCE_NAME_SUFFIX']}"
        inference_instance_type = os.environ["BATCH_INFERENCE_INSTANCE_TYPE"]
        inference_instance_count = int(os.environ["BATCH_INFERENCE_INSTANCE_COUNT"])
    except KeyError:
        response["statusCode"] = 500
        response["body"] = json.dumps(
            {"message": "Internal server error determining configuration options."}
        )
        return response

    get_sagemaker_client().create_transform_job(
        TransformJobName=transform_job_name,
        ModelName=get_latest_deployable_model_name(),
        BatchStrategy="MultiRecord",
        TransformInput={
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
        TransformOutput={
            "S3OutputPath": output_data_s3_uri,
            "Accept": "text/csv",
            "AssembleWith": "Line",
            "KmsKeyId": inference_data_bucket_kms_key_id,
        },
        TransformResources={
            "InstanceType": inference_instance_type,  # type: ignore[typeddict-item]
            "InstanceCount": inference_instance_count,
        },
        DataProcessing={
            "InputFilter": "$[1:]",
            "OutputFilter": "$",
            "JoinSource": "None",
        },
    )
    response["statusCode"] = 200
    response["body"] = json.dumps(
        {
            "transform-job-name": transform_job_name,
        }
    )

    return response


API_DISPATCHER: Dict[str, Dict[str, Callable[[Any, Any], Dict[str, Any]]]] = {
    "/predict": {
        "POST": get_prediction,
    },
    "/batch-predict": {
        "POST": start_batch_prediction,
    },
}


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    response = API_DISPATCHER[event["resource"]][event["httpMethod"]](event, context)
    return response
