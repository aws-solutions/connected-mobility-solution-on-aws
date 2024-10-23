# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import csv
import os
from functools import lru_cache
from io import StringIO
from typing import TYPE_CHECKING, Annotated, Any, Dict, List

# AWS Libraries
import boto3
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import BedrockAgentResolver
from aws_lambda_powertools.event_handler.openapi.params import Body, Query
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.config import Config

if TYPE_CHECKING:
    # Third Party Libraries
    from mypy_boto3_s3.client import S3Client
else:
    S3Client = object

tracer = Tracer()
logger = Logger()
app = BedrockAgentResolver()


@lru_cache(maxsize=1)
def get_s3_client() -> S3Client:
    return boto3.client(
        "s3", config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"])
    )


def get_csv_object_from_s3(bucket_name: str, object_key: str) -> List[List[Any]]:
    response = get_s3_client().get_object(Bucket=bucket_name, Key=object_key)
    content = response["Body"].read().decode("utf-8")
    return list(csv.reader(StringIO(content)))


@app.get(
    "/vehicle_maintenance_status",
    description="Gets the maintenance status of a vehicle with a given VIN.",
)
def get_vehicle_maintenance_status(
    vin: Annotated[
        str, Query(max_length=20, strict=True, description="Vehicle VIN number.")
    ],
) -> Annotated[bool, Body(description="Does the vehicle need maintenance?")]:
    inference_data_s3_bucket_name = os.environ["INFERENCE_DATA_S3_BUCKET_NAME"]
    inference_input_data_s3_key = os.environ["INFERENCE_INPUT_DATA_S3_KEY"]
    inference_output_data_s3_key = os.environ["INFERENCE_OUTPUT_DATA_S3_KEY"]

    input_data_csv = get_csv_object_from_s3(
        bucket_name=inference_data_s3_bucket_name,
        object_key=inference_input_data_s3_key,
    )
    output_data_csv = get_csv_object_from_s3(
        bucket_name=inference_data_s3_bucket_name,
        object_key=inference_output_data_s3_key,
    )

    matched_vin_indices = [
        idx for idx, row in enumerate(input_data_csv) if vin == row[0]
    ]
    if len(matched_vin_indices) > 0:
        vin_index = matched_vin_indices[0]
    else:
        vin_index = -1
        raise ValueError("VIN not found in the prediction results.")

    prediction_output_strings = output_data_csv[vin_index]
    prediction_output_floats = [float(item) for item in prediction_output_strings]
    fault_code_index = max(
        range(len(prediction_output_floats)), key=prediction_output_floats.__getitem__
    )
    return fault_code_index > 0


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    return app.resolve(event, context)


if __name__ == "__main__":
    print(app.get_openapi_json_schema(openapi_version="3.0.3"))
