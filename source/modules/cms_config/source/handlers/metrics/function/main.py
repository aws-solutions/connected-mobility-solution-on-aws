# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import datetime
import os
from functools import lru_cache
from typing import Any, Dict

# AWS Libraries
import boto3
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.config import Config

# Connected Mobility Solution on AWS
from .lib import data_firehose_helper, metrics_publish, s3_helper

tracer = Tracer()
logger = Logger()


@lru_cache(maxsize=128)
def get_resourcegroupstaggingapi_client() -> Any:
    return boto3.client(
        "resourcegroupstaggingapi",
        config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"]),
    )


@lru_cache(maxsize=128)
def get_cloudwatch_client() -> Any:
    return boto3.client(
        "cloudwatch", config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"])
    )


@tracer.capture_lambda_handler
def handler(event: Dict[str, Any], context: LambdaContext) -> None:

    s3_storage_bytes = None
    data_firehose_metrics = None

    resourcegroupstaggingapi = get_resourcegroupstaggingapi_client()
    cloudwatch = get_cloudwatch_client()

    config = build_config()

    try:

        s3_storage_bytes = s3_helper.get_cms_s3_total_storage_in_use(
            config, resourcegroupstaggingapi, cloudwatch
        )

    except Exception as err:  # pylint: disable=W0718
        logger.error("Failed to record S3 metrics")
        logger.error(err)

    try:
        data_firehose_metrics = data_firehose_helper.get_cms_data_firehose_utilization(
            config, resourcegroupstaggingapi, cloudwatch
        )

    except Exception as err:  # pylint: disable=W0718
        logger.error("Failed to record Data Firehose metrics")
        logger.error(err)

    try:

        metric: Dict[str, Any] = {
            "Type": "CMSDeploymentMetricScrape",
        }

        if data_firehose_metrics:
            metric["DailyNumberOfDeliveryStreamsUsed"] = data_firehose_metrics[
                "total_num_data_streams_in_use_on_day"
            ]
            metric["DailyIncomingPutRequests"] = data_firehose_metrics[
                "total_put_requests_per_day"
            ]

        if s3_storage_bytes:
            metric["SumAllBucketsSizeBytes"] = s3_storage_bytes

        metrics_publish.write_metric(config, metric, config["metric_timestamp"])
    except Exception as err:  # pylint: disable=W0718
        logger.error("Failed to publish metrics", exc_info=True)


def build_config() -> Dict[str, Any]:
    config: Dict[str, Any] = {}

    utc_today = datetime.datetime.utcnow().date()

    config["today"] = datetime.datetime(
        utc_today.year,
        utc_today.month,
        utc_today.day,
        tzinfo=datetime.timezone.utc,
    )
    config["yesterday"] = config["today"] - datetime.timedelta(days=1)
    config["metric_timestamp"] = datetime.datetime.now()

    config["solution_id"] = os.environ["SOLUTION_ID"]
    config["solution_version"] = os.environ["SOLUTION_VERSION"]
    config["account_id"] = os.environ["AWS_ACCOUNT_ID"]
    config["region"] = os.environ["AWS_REGION"]
    config["metrics_solution_url"] = os.environ["METRICS_SOLUTION_URL"]
    config["deployment_uuid"] = os.environ["DEPLOYMENT_UUID"]

    return config
