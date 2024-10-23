# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json
from datetime import datetime
from typing import Any, Dict
from unittest.mock import MagicMock

# Third Party Libraries
import pytest

# AWS Libraries
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.stub import Stubber

# CMS Common Library
from cms_common.enums.custom_resource import (
    CustomResourceRequestType,
    CustomResourceStatusType,
)

# Connected Mobility Solution on AWS
from ..lib.custom_resource_type_enum import CustomResourceFunctionType
from ..main import handler, send_cloud_formation_response


def test_custom_resource_handler_invalid_resource_type(
    custom_resource_event: Dict[str, Any],
    context: LambdaContext,
    mocker: MagicMock,
) -> None:
    mocked_requests: MagicMock = mocker.patch("requests.put")
    custom_resource_event["ResourceProperties"]["Resource"] = "InvalidResourceType"
    response = handler(custom_resource_event, context)

    mocked_requests.assert_called_once()
    assert response["Status"] == CustomResourceStatusType.FAILED.value


def test_send_cloud_formation_response(
    custom_resource_event: Dict[str, Any], mocker: MagicMock
) -> None:
    mocked_requests: MagicMock = mocker.patch("requests.put")

    input_response = {
        "Status": "SUCCESS",
        "Data": None,
    }
    reason = "test-reason"

    expected_response = json.dumps(
        {
            "Status": input_response["Status"],
            "Reason": reason,
            "PhysicalResourceId": custom_resource_event["LogicalResourceId"],
            "StackId": custom_resource_event["StackId"],
            "RequestId": custom_resource_event["RequestId"],
            "LogicalResourceId": custom_resource_event["LogicalResourceId"],
            "Data": input_response["Data"],
        }
    )
    headers = {"Content-Type": "application/json"}

    send_cloud_formation_response(custom_resource_event, input_response, reason)

    mocked_requests.assert_called_with(
        custom_resource_event["ResponseURL"],
        data=expected_response,
        headers=headers,
        timeout=60,
    )


@pytest.mark.parametrize("send_cf_response", [True, False])
def test_send_cloud_formation_response_flag(
    custom_resource_event: Dict[str, Any],
    context: LambdaContext,
    mocker: MagicMock,
    send_cf_response: bool,
) -> None:
    mocked_requests: MagicMock = mocker.patch("requests.put")
    if not send_cf_response:
        custom_resource_event["ResourceProperties"]["DoNotSendCFResponse"] = 1
    handler(custom_resource_event, context)
    assert mocked_requests.call_count == int(send_cf_response)


def test_get_vpc_endpoint_id_on_create(
    mock_boto3_client: MagicMock,
    opensearchserverless_client_stubber: Stubber,
    context: LambdaContext,
    custom_resource_event: Dict[str, Any],
    custom_resource_setup: Any,
    mocker: MagicMock,
) -> None:
    mocked_requests: MagicMock = mocker.patch("requests.put")

    vpc_endpoint_name = "test-vpc-endpoint-name"
    vpc_endpoint_id = "test-vpc-endpoint-id"

    custom_resource_event["RequestType"] = CustomResourceRequestType.CREATE.value
    custom_resource_event["ResourceProperties"] = {
        "Resource": CustomResourceFunctionType.GET_AOSS_VPC_ENDPOINT_ID.value,
        "VpcEndpointName": vpc_endpoint_name,
    }

    list_vpc_endpoints_params: Dict[str, Any] = {}
    list_vpc_endpoints_response = {
        "nextToken": "",
        "vpcEndpointSummaries": [
            {"id": vpc_endpoint_id, "name": vpc_endpoint_name, "status": "ACTIVE"},
        ],
    }
    opensearchserverless_client_stubber.add_response(
        "list_vpc_endpoints", list_vpc_endpoints_response, list_vpc_endpoints_params
    )
    mock_boto3_client(
        "opensearchserverless", return_value=opensearchserverless_client_stubber.client
    )

    response = handler(custom_resource_event, context)

    opensearchserverless_client_stubber.assert_no_pending_responses()
    mocked_requests.assert_called_once()
    assert response["Status"] == CustomResourceStatusType.SUCCESS.value
    assert response["Data"]["vpce_id"] == vpc_endpoint_id


def test_ingest_bedrock_data_source_on_create(
    mock_boto3_client: MagicMock,
    bedrock_agent_client_stubber: Stubber,
    context: LambdaContext,
    custom_resource_ingest_bedrock_data_source_event: Dict[str, Any],
    custom_resource_setup: Any,
    mocker: MagicMock,
) -> None:
    mocked_requests: MagicMock = mocker.patch("requests.put")

    custom_resource_ingest_bedrock_data_source_event[
        "RequestType"
    ] = CustomResourceRequestType.CREATE.value

    start_ingestion_job_params = {
        "dataSourceId": custom_resource_ingest_bedrock_data_source_event[
            "ResourceProperties"
        ]["DataSourceId"],
        "knowledgeBaseId": custom_resource_ingest_bedrock_data_source_event[
            "ResourceProperties"
        ]["KnowledgeBaseId"],
        "description": f'{custom_resource_ingest_bedrock_data_source_event["ResourceProperties"]["DataSourceId"]} - ingest data source',
    }
    start_ingestion_job_response = {
        "ingestionJob": {
            "dataSourceId": custom_resource_ingest_bedrock_data_source_event[
                "ResourceProperties"
            ]["DataSourceId"],
            "description": f'{custom_resource_ingest_bedrock_data_source_event["ResourceProperties"]["DataSourceId"]} - ingest data source',
            "ingestionJobId": "test-ingestion-job-id",
            "knowledgeBaseId": custom_resource_ingest_bedrock_data_source_event[
                "ResourceProperties"
            ]["KnowledgeBaseId"],
            "startedAt": datetime(2024, 4, 20),
            "status": "COMPLETE",
            "updatedAt": datetime(2024, 4, 20),
        }
    }

    bedrock_agent_client_stubber.add_response(
        "start_ingestion_job",
        start_ingestion_job_response,
        start_ingestion_job_params,
    )
    mock_boto3_client("bedrock-agent", return_value=bedrock_agent_client_stubber.client)

    response = handler(custom_resource_ingest_bedrock_data_source_event, context)

    bedrock_agent_client_stubber.assert_no_pending_responses()
    mocked_requests.assert_called_once()
    assert response["Status"] == CustomResourceStatusType.SUCCESS.value
