# -*- coding: utf-8 -*-

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import random
from typing import Any, Dict

# AWS Libraries
import botocore
from botocore.stub import Stubber

# Connected Mobility Solution on AWS
from ...lib import data_firehose_helper
from ...main import build_config
from ...tests import UnitTestCommon
from .fixture_metrics_function_lib import (
    get_halfway_yesterday_time_utc,
    get_solution_resource_tags,
)


class TestHandler(UnitTestCommon):
    def configure_cw_metrics_client_stubber(
        self, data_firehose_metrics_response: Dict[str, Any]
    ) -> Any:
        stubbed_cw_client = botocore.session.get_session().create_client("cloudwatch")

        stubber = Stubber(stubbed_cw_client)

        stubber.add_response("get_metric_data", data_firehose_metrics_response)

        stubber.activate()

        return stubbed_cw_client

    def configure_resourcegroupstaggingapi_stubber(
        self, config: Dict[str, Any], response: Dict[str, Any]
    ) -> Any:
        stubbed_resourcegroupstaggingapi_client = (
            botocore.session.get_session().create_client("resourcegroupstaggingapi")
        )

        stubber = Stubber(stubbed_resourcegroupstaggingapi_client)

        stubber.add_response(
            "get_resources",
            response,
            {
                "TagFilters": [
                    {"Key": "Solutions:SolutionID", "Values": [config["solution_id"]]},
                    {
                        "Key": "Solutions:DeploymentUUID",
                        "Values": [config["deployment_uuid"]],
                    },
                ],
                "ResourceTypeFilters": ["firehose:deliverystream"],
            },
        )

        stubber.activate()

        return stubbed_resourcegroupstaggingapi_client

    def test_get_cms_data_firehose_utilization(self) -> None:
        config = build_config()

        total_num_data_streams_in_use_on_day = 5

        resourcegroupstagingapi_response = (
            generate_resourcegroupstaggingapi_firehose_response(
                total_num_data_streams_in_use_on_day,
                config["solution_id"],
                config["deployment_uuid"],
                config["region"],
                config["account_id"],
            )
        )

        data_firehose_metrics_response = generate_data_firehose_metrics_response(
            resourcegroupstagingapi_response
        )

        stubbed_resourcegroupstaggingapi_client = (
            self.configure_resourcegroupstaggingapi_stubber(
                config, resourcegroupstagingapi_response
            )
        )

        stubbed_cw_metrics_client = self.configure_cw_metrics_client_stubber(
            data_firehose_metrics_response
        )

        result = data_firehose_helper.get_cms_data_firehose_utilization(
            config, stubbed_resourcegroupstaggingapi_client, stubbed_cw_metrics_client
        )

        sum_of_firehose_puts = sum(
            firehose_put_info["Values"][0]
            for firehose_put_info in data_firehose_metrics_response["MetricDataResults"]
        )

        self.assertEqual(sum_of_firehose_puts, result["total_put_requests_per_day"])
        self.assertEqual(
            total_num_data_streams_in_use_on_day,
            result["total_num_data_streams_in_use_on_day"],
        )

    def test_get_cms_data_firehose_no_utilization(self) -> None:
        config = build_config()

        total_num_data_streams_in_use_on_day = 0

        resourcegroupstagingapi_response = (
            generate_resourcegroupstaggingapi_firehose_response(
                total_num_data_streams_in_use_on_day,
                config["solution_id"],
                config["deployment_uuid"],
                config["region"],
                config["account_id"],
            )
        )

        stubbed_resourcegroupstaggingapi_client = (
            self.configure_resourcegroupstaggingapi_stubber(
                config, resourcegroupstagingapi_response
            )
        )

        data_firehose_metrics_response = generate_data_firehose_metrics_empty_response()

        stubbed_cw_metrics_client = self.configure_cw_metrics_client_stubber(
            data_firehose_metrics_response
        )

        result = data_firehose_helper.get_cms_data_firehose_utilization(
            config, stubbed_resourcegroupstaggingapi_client, stubbed_cw_metrics_client
        )

        self.assertEqual(0, result["total_put_requests_per_day"])
        self.assertEqual(0, result["total_num_data_streams_in_use_on_day"])


def generate_data_firehose_metrics_response(
    resourcegroupstaggingapi_firehose_response: Dict[str, Any]
) -> Dict[str, Any]:
    utc_halfway_yesterday_time = get_halfway_yesterday_time_utc()

    result: Dict[str, Any] = {"MetricDataResults": [], "Messages": []}

    for i in range(
        0, len(resourcegroupstaggingapi_firehose_response["ResourceTagMappingList"])
    ):
        result["MetricDataResults"].append(
            {
                "Id": f"dailyputrequests_{i}",
                "Label": "IncomingPutRequests",
                "Timestamps": [utc_halfway_yesterday_time],
                "Values": [random.randint(1000, 5000)],
                "StatusCode": "Complete",
            }
        )

    return result


def generate_data_firehose_metrics_empty_response() -> Dict[str, Any]:
    return {
        "MetricDataResults": [],
        "Messages": [],
    }


def generate_resourcegroupstaggingapi_firehose_response(
    num_delivery_streams: int,
    solution_id: str,
    deployment_uuid: str,
    region: str,
    account_id: str,
) -> Dict[str, Any]:
    response: Dict[str, Any] = {"PaginationToken": "", "ResourceTagMappingList": []}

    for i in range(0, num_delivery_streams):
        response["ResourceTagMappingList"].append(
            {
                "ResourceARN": f"arn:aws:firehose:{region}:{account_id}:deliverystream/stream_{i}",
                "Tags": get_solution_resource_tags(
                    solution_id, deployment_uuid, f"module-{i}"
                ),
            }
        )

    return response
