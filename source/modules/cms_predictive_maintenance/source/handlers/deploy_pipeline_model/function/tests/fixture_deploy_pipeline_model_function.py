# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any, Dict

# Third Party Libraries
import pytest

# Connected Mobility Solution on AWS
from ..main import get_sagemaker_client


@pytest.fixture(name="deploy_pipeline_model_setup")
def fixture_deploy_pipeline_model_setup() -> Any:
    get_sagemaker_client.cache_clear()


@pytest.fixture(name="deploy_pipeline_model_event")
def fixture_deploy_pipeline_model_event() -> Dict[str, Any]:
    return {
        "ResourceNameSuffix": "test",
        "ModelPackageGroupName": "test-group",
        "PipelineExecutionRoleArn": "arn:aws:iam::123456789012:role/test-role",
        "InferenceInstanceType": "ml.t2.medium",
        "InferenceInstanceCount": 1,
        "EndpointName": "test-endpoint",
    }
