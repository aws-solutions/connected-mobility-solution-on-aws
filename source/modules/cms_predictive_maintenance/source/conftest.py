# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# pylint: disable=W0611

# Standard Library
import os
from datetime import datetime, timezone
from typing import Any, Dict, Generator, List, Optional, cast
from unittest.mock import MagicMock, patch

# Third Party Libraries
import pytest

# AWS Libraries
import botocore
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.stub import Stubber

# Connected Mobility Solution on AWS
from .handlers.authorization.function.tests.fixture_authorization_function import (
    fixture_authorization_allow_policy,
    fixture_authorization_deny_policy,
    fixture_invalid_authorization_event,
    fixture_reset_api_booleans,
    fixture_valid_authorization_event,
    mock_env_for_authorization,
)
from .handlers.custom_resource.function.tests.fixture_custom_resource_function import (
    fixture_custom_resource_event,
    fixture_custom_resource_ingest_bedrock_data_source_event,
    fixture_custom_resource_setup,
)
from .handlers.deploy_pipeline_model.function.tests.fixture_deploy_pipeline_model_function import (
    fixture_deploy_pipeline_model_event,
    fixture_deploy_pipeline_model_setup,
)
from .handlers.predict_api.function.tests.fixture_predict_api_function import (
    fixture_batch_predict_post_event,
    fixture_predict_api_env_vars,
    fixture_predict_api_setup,
    fixture_predict_post_event,
)
from .infrastructure.tests.fixture_infrastructure import (
    fixture_snapshot_json_with_matcher,
)


def boto3_client_selector_side_effect(
    bedrock_agent_client: MagicMock,
    opensearchserverless_client: MagicMock,
    s3_client: MagicMock,
    sagemaker_client: MagicMock,
    sagemaker_runtime_client: MagicMock,
    dynamodb_client: MagicMock,
    client_type: str,
    *args: List[Any],  # catch unused args from boto3.client
    return_value: Optional[
        Any
    ] = None,  # injected return_value for unit test purposes, not in boto3.client interface
    **kwargs: Dict[str, Any],  # catch unused kwargs from boto3.client
) -> Any:
    match client_type:
        case "bedrock-agent":
            selected_client = bedrock_agent_client
        case "opensearchserverless":
            selected_client = opensearchserverless_client
        case "s3":
            selected_client = s3_client
        case "sagemaker":
            selected_client = sagemaker_client
        case "sagemaker-runtime":
            selected_client = sagemaker_runtime_client
        case "dynamodb":
            selected_client = dynamodb_client
        case _:
            raise AttributeError(
                f"Unsupported boto3 client type specified: {client_type}"
            )

    if return_value is not None:
        selected_client.return_value = return_value

    return selected_client.return_value


@pytest.fixture(name="mock_boto3_client")
def fixture_mock_boto3_client() -> Generator[MagicMock, None, None]:
    bedrock_agent_client = MagicMock()
    opensearchserverless_client = MagicMock()
    s3_client = MagicMock()
    sagemaker_client = MagicMock()
    sagemaker_runtime_client = MagicMock()
    dynamodb_client = MagicMock()

    with patch(
        "boto3.client",
        side_effect=lambda *args, **kwargs: boto3_client_selector_side_effect(
            bedrock_agent_client,
            opensearchserverless_client,
            s3_client,
            sagemaker_client,
            sagemaker_runtime_client,
            dynamodb_client,
            *args,
            **kwargs,
        ),
    ) as client:
        yield client


@pytest.fixture(name="bedrock_agent_client_stubber")
def fixture_bedrock_agent_stubber() -> Generator[Stubber, None, None]:
    bedrock_agent_client = botocore.session.get_session().create_client("bedrock-agent")
    with Stubber(bedrock_agent_client) as stubber:
        yield stubber


@pytest.fixture(name="opensearchserverless_client_stubber")
def fixture_opensearchserverless_client_stubber() -> Generator[Stubber, None, None]:
    opensearchserverless_client = botocore.session.get_session().create_client(
        "opensearchserverless"
    )
    with Stubber(opensearchserverless_client) as stubber:
        yield stubber


@pytest.fixture(name="s3_client_stubber")
def fixture_s3_client_stubber() -> Generator[Stubber, None, None]:
    s3_client = botocore.session.get_session().create_client("s3")
    with Stubber(s3_client) as stubber:
        yield stubber


@pytest.fixture(name="sagemaker_client_stubber")
def fixture_sagemaker_client_stubber() -> Generator[Stubber, None, None]:
    sagemaker_client = botocore.session.get_session().create_client("sagemaker")
    with Stubber(sagemaker_client) as stubber:
        yield stubber


@pytest.fixture(name="sagemaker_runtime_client_stubber")
def fixture_sagemaker_runtime_client_stubber() -> Generator[Stubber, None, None]:
    sagemaker_client = botocore.session.get_session().create_client("sagemaker-runtime")
    with Stubber(sagemaker_client) as stubber:
        yield stubber


@pytest.fixture(name="dynamodb_client_stubber")
def fixture_dynamodb_client_stubber() -> Generator[Stubber, None, None]:
    dynamodb_client = botocore.session.get_session().create_client("dynamodb")
    with Stubber(dynamodb_client) as stubber:
        yield stubber


@pytest.fixture(name="context")
def fixture_context() -> LambdaContext:
    class MockLambdaContext:
        def __init__(self) -> None:
            self.function_name = "test"
            self.memory_limit_in_mb = 128
            self.invoked_function_arn = (
                "arn:aws:lambda:us-east-1:11111111111:function:test"
            )
            self.aws_request_id = "52fdfc07-2182-154f-163f-5f0f9a621d72"
            self.log_stream_name = "TestLogStream"

    return cast(LambdaContext, MockLambdaContext())


# Prevents boto from accidentally using default AWS credentials if not mocked
@pytest.fixture(name="aws_credentials_env_vars", scope="session")
def fixture_aws_credentials_env_vars() -> Dict[str, str]:
    return {
        "AWS_ACCESS_KEY_ID": "testing",  # nosec
        "AWS_SECRET_ACCESS_ID": "testing",  # nosec
        "AWS_SECURITY_TOKEN": "testing",  # nosec
        "AWS_SESSION_TOKEN": "testing",  # nosec
        "AWS_SECRET_ACCESS_KEY": "testing",  # nosec
        "AWS_DEFAULT_REGION": "us-east-1",  # nosec
    }


@pytest.fixture(name="mock_module_env_vars", scope="session")
def fixture_mock_module_env_vars() -> Dict[str, str]:
    return {
        "APPLICATION_TYPE": "test-application-type",
        "SOLUTION_ID": "test-solution-id",
        "SOLUTION_NAME": "test-solution-name",
        "SOLUTION_VERSION": "v0.0.0",
        "S3_ASSET_BUCKET_BASE_NAME": "test-bucket-name",
        "S3_ASSET_KEY_PREFIX": "test-key-prefix",
        "USER_AGENT_STRING": "test-user-agent",
    }


@pytest.fixture(scope="session", autouse=True)
def fixture_mock_env_vars(
    aws_credentials_env_vars: Dict[str, str], mock_module_env_vars: Dict[str, str]
) -> Generator[None, None, None]:
    env_vars = {
        **aws_credentials_env_vars,
        **mock_module_env_vars,
    }
    with patch.dict(os.environ, env_vars):
        yield


@pytest.fixture(name="mock_datetime")
def fixture_mock_datetime(monkeypatch: Any) -> Any:
    class MockDatetime:
        FIXED_DATETIME = datetime(2023, 1, 1, 10, 0, 0, tzinfo=timezone.utc)

        @classmethod
        def now(cls: Any, tz: Optional[str] = None) -> Any:
            return cls.FIXED_DATETIME

        @classmethod
        def utcnow(cls: Any) -> Any:
            return cls.FIXED_DATETIME

    monkeypatch.setattr("datetime.datetime", MockDatetime)
    return MockDatetime
