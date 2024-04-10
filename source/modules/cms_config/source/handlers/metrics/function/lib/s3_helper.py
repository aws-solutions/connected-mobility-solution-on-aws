# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import datetime
from typing import Any, Dict

# AWS Libraries
from aws_lambda_powertools import Logger, Tracer

tracer = Tracer()
logger = Logger()

SECONDS_IN_DAY = 86400


@tracer.capture_method()
def get_cms_s3_total_storage_in_use(
    config: Dict[str, Any],
    resourcegroupstaggingapi: Any,
    cloudwatch_client: Any,
) -> int:
    s3_buckets_resources = resourcegroupstaggingapi.get_resources(
        TagFilters=[
            {"Key": "Solutions:SolutionID", "Values": [config["solution_id"]]},
            {"Key": "Solutions:DeploymentUUID", "Values": [config["deployment_uuid"]]},
        ],
        ResourceTypeFilters=["s3:bucket"],
    )

    s3_bucket_arns = [
        resource_map["ResourceARN"]
        for resource_map in s3_buckets_resources["ResourceTagMappingList"]
    ]
    s3_bucket_metrics_queries = [
        __create_s3_bucket_metric_query(
            s3_bucket_arn, s3_bucket_arn_index, config["account_id"]
        )
        for s3_bucket_arn_index, s3_bucket_arn in enumerate(s3_bucket_arns)
    ]

    logger.debug("S3 Metrics generated queries:")
    logger.debug(s3_bucket_metrics_queries)

    response = cloudwatch_client.get_metric_data(
        MetricDataQueries=s3_bucket_metrics_queries,
        # Sometimes S3 metrics are not generated each day, grab the day before as well.
        StartTime=config["yesterday"] - datetime.timedelta(days=1),
        EndTime=config["today"],
        MaxDatapoints=1000,
        LabelOptions={"Timezone": "+0000"},
        ScanBy="TimestampDescending",
    )

    total_storage_in_use = int(
        sum(
            __get_latest_bytes_from_bucket_metric(bucket_metrics)
            for bucket_metrics in response["MetricDataResults"]
        )
    )

    yesterday_date_iso = config["yesterday"].date().isoformat()

    logger.info(
        "S3 Storage Byte Info for %s: %f", yesterday_date_iso, total_storage_in_use
    )

    return total_storage_in_use


def __create_s3_bucket_metric_query(
    bucket_arn: str, index: int, account_id: str
) -> Dict[str, Any]:
    bucket_name = bucket_arn.split(":")[-1]

    return {
        "Id": f"bucket_{index}",
        "MetricStat": {
            "Metric": {
                "Namespace": "AWS/S3",
                "MetricName": "BucketSizeBytes",
                "Dimensions": [
                    {"Name": "StorageType", "Value": "StandardStorage"},
                    {
                        "Name": "BucketName",
                        "Value": bucket_name,
                    },
                ],
            },
            "Period": SECONDS_IN_DAY,
            "Stat": "Average",
            "Unit": "Bytes",
        },
        "Label": "BucketSizeBytes",
        "ReturnData": True,
        "AccountId": account_id,
    }


def __get_latest_bytes_from_bucket_metric(bucket_metrics: Dict[str, Any]) -> int:
    try:
        return int(bucket_metrics["Values"][0])
    except (IndexError, ValueError):
        logger.warning(
            "Empty list or None value at end of list. Most likely a new or empty bucket."
        )
        return 0
    except KeyError as err:
        logger.error("Expected 'Values', but dict was missing it")
        logger.error(err)
        raise
