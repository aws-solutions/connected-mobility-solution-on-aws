# -*- coding: utf-8 -*-

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import random
from typing import Any, Dict

# Third Party Libraries
import botocore
from botocore.stub import Stubber

# Connected Mobility Solution on AWS
from ...lib import s3_helper
from ...main import build_config
from .. import (
    UnitTestCommon,
    get_halfway_yesterday_time_utc,
    get_solution_resource_tags,
)


class TestHandler(UnitTestCommon):
    def configure_cw_metrics_client_stubber(
        self, s3_metrics_response: Dict[str, Any]
    ) -> Any:
        stubbed_cw_client = botocore.session.get_session().create_client("cloudwatch")

        stubber = Stubber(stubbed_cw_client)

        stubber.add_response("get_metric_data", s3_metrics_response)

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
                "ResourceTypeFilters": ["s3:bucket"],
            },
        )

        stubber.activate()

        return stubbed_resourcegroupstaggingapi_client

    def test_get_s3_metrics_gets_sum_of_bucket_sizes(self) -> None:
        config = build_config()

        resourcegroupstagingapi_response = (
            generate_resourcegroupstaggingapi_s3_response(
                2, config["solution_id"], config["deployment_uuid"]
            )
        )
        s3_metrics_response = generate_s3_metrics_response(
            resourcegroupstagingapi_response
        )
        stubbed_resourcegroupstaggingapi_client = (
            self.configure_resourcegroupstaggingapi_stubber(
                config, resourcegroupstagingapi_response
            )
        )
        stubbed_cw_metrics_client = self.configure_cw_metrics_client_stubber(
            s3_metrics_response
        )

        result = s3_helper.get_cms_s3_total_storage_in_use(
            config, stubbed_resourcegroupstaggingapi_client, stubbed_cw_metrics_client
        )

        sum_of_bucket_sizes = sum(
            bucket_info["Values"][0]
            for bucket_info in s3_metrics_response["MetricDataResults"]
        )

        self.assertEqual(sum_of_bucket_sizes, result)

    def test_get_s3_metrics_gets_zero_if_no_buckets(self) -> None:
        config = build_config()

        resourcegroupstagingapi_response = (
            generate_resourcegroupstaggingapi_s3_response(
                0, config["solution_id"], config["deployment_uuid"]
            )
        )
        s3_metrics_response = generate_s3_metrics_response(
            resourcegroupstagingapi_response
        )
        stubbed_resourcegroupstaggingapi_client = (
            self.configure_resourcegroupstaggingapi_stubber(
                config, resourcegroupstagingapi_response
            )
        )
        stubbed_cw_metrics_client = self.configure_cw_metrics_client_stubber(
            s3_metrics_response
        )

        result = s3_helper.get_cms_s3_total_storage_in_use(
            config, stubbed_resourcegroupstaggingapi_client, stubbed_cw_metrics_client
        )

        sum_of_bucket_sizes = 0  # There should be no size since theres no buckets

        self.assertEqual(sum_of_bucket_sizes, result)


def generate_resourcegroupstaggingapi_s3_response(
    num_buckets: int, solution_id: str, deployment_uuid: str
) -> Dict[str, Any]:
    response: Dict[str, Any] = {"PaginationToken": "", "ResourceTagMappingList": []}

    for i in range(0, num_buckets):
        response["ResourceTagMappingList"].append(
            {
                "ResourceARN": f"arn:aws:s3:::cms-bucket-{i}",
                "Tags": get_solution_resource_tags(
                    solution_id, deployment_uuid, f"module-{i}"
                ),
            }
        )

    return response


def generate_s3_metrics_response(
    resourcegroupstaggingapi_s3_response: Dict[str, Any],
) -> Dict[str, Any]:
    utc_halfway_yesterday_time = get_halfway_yesterday_time_utc()

    result: Dict[str, Any] = {"MetricDataResults": [], "Messages": []}

    for i in range(
        0, len(resourcegroupstaggingapi_s3_response["ResourceTagMappingList"])
    ):
        result["MetricDataResults"].append(
            {
                "Id": f"bucket_{i}",
                "Label": "BucketSizeBytes",
                "Timestamps": [utc_halfway_yesterday_time],
                "Values": [random.randint(10000, 100000000)],
                "StatusCode": "Complete",
            }
        )

    return result
