# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json
import os
from typing import Any, Dict, Generator
from unittest.mock import patch

# Third Party Libraries
import pytest

# Connected Mobility Solution on AWS
from ..main import get_sagemaker_client, get_sagemaker_runtime_client


@pytest.fixture(name="predict_api_setup")
def fixture_predict_api_setup() -> Any:
    get_sagemaker_client.cache_clear()
    get_sagemaker_runtime_client.cache_clear()


@pytest.fixture(name="predict_api_env_vars")
def fixture_predict_api_env_vars() -> Generator[None, Any, Any]:
    env_vars = {
        "SAGEMAKER_MODEL_ENDPOINT_NAME": "test-model-endpoint",
        "RESOURCE_NAME_SUFFIX": "cms-predictive-maintenance",
        "BATCH_INFERENCE_DATA_S3_BUCKET_NAME": "test-bucket",
        "BATCH_INFERENCE_DATA_OUTPUT_S3_KEY_PREFIX": "inference/",
        "BATCH_INFERENCE_INSTANCE_TYPE": "ml.m5.xlarge",
        "BATCH_INFERENCE_INSTANCE_COUNT": "1",
    }

    with patch.dict(os.environ, env_vars):
        yield


@pytest.fixture(name="predict_post_event")
def fixture_predict_post_event() -> Dict[str, Any]:
    return {
        "resource": "/predict",
        "httpMethod": "POST",
        "body": json.dumps({"input": "1,2,3,4"}),
    }


@pytest.fixture(name="batch_predict_post_event")
def fixture_batch_predict_post_event() -> Dict[str, Any]:
    return {
        "resource": "/batch-predict",
        "httpMethod": "POST",
        "body": json.dumps({"input_data_s3_key": "inference/test.csv"}),
    }
