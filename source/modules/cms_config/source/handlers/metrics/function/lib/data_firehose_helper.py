# -*- coding: utf-8 -*-

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any, Dict

# AWS Libraries
from aws_lambda_powertools import Logger, Tracer

tracer = Tracer()
logger = Logger()

SECONDS_IN_DAY = 86400


@tracer.capture_method()
def get_cms_data_firehose_utilization(
    config: Dict[str, Any],
    resourcegroupstaggingapi: Any,
    cloudwatch_client: Any,
) -> Dict[str, Any]:
    data_firehose_resources = resourcegroupstaggingapi.get_resources(
        TagFilters=[
            {"Key": "Solutions:SolutionID", "Values": [config["solution_id"]]},
            {"Key": "Solutions:DeploymentUUID", "Values": [config["deployment_uuid"]]},
        ],
        ResourceTypeFilters=["firehose:deliverystream"],
    )

    data_firehose_arns = [
        resource_map["ResourceARN"]
        for resource_map in data_firehose_resources["ResourceTagMappingList"]
    ]

    data_firehose_metric_queries = [
        __create_data_firehose_metric_query(
            data_firehose_arn, data_firehose_index, config["account_id"]
        )
        for data_firehose_index, data_firehose_arn in enumerate(data_firehose_arns)
    ]

    response = cloudwatch_client.get_metric_data(
        MetricDataQueries=data_firehose_metric_queries,
        StartTime=config["yesterday"],
        EndTime=config["today"],
        MaxDatapoints=1000,
        LabelOptions={"Timezone": "+0000"},
        ScanBy="TimestampDescending",
    )

    total_put_requests_per_day = int(
        sum(
            __get_put_requests_per_day(firehose_metrics)
            for firehose_metrics in response["MetricDataResults"]
        )
    )

    total_num_data_streams_in_use_on_day = len(response["MetricDataResults"])

    yesterday_date_iso = config["yesterday"].date().isoformat()
    logger.info(
        "Data Firehose Put Utilization for %s: %f",
        yesterday_date_iso,
        total_put_requests_per_day,
    )
    logger.info(
        "Data Firehose Number of Delivery Streams Used on %s: %f",
        yesterday_date_iso,
        total_num_data_streams_in_use_on_day,
    )

    return {
        "total_put_requests_per_day": total_put_requests_per_day,
        "total_num_data_streams_in_use_on_day": total_num_data_streams_in_use_on_day,
    }


def __create_data_firehose_metric_query(
    delivery_stream_arn: str, index: int, account_id: str
) -> Dict[str, Any]:

    delivery_stream_name = delivery_stream_arn.split(":")[-1]

    return {
        "Id": f"dailyputrequests_{index}",
        "MetricStat": {
            "Metric": {
                "Namespace": "AWS/Firehose",
                "MetricName": "IncomingPutRequests",
                "Dimensions": [
                    {"Name": "DeliveryStreamName", "Value": delivery_stream_name},
                ],
            },
            "Period": SECONDS_IN_DAY,
            "Stat": "Sum",
            "Unit": "Count",
        },
        "Label": "IncomingPutRequests",
        "ReturnData": True,
        "AccountId": account_id,
    }


def __get_put_requests_per_day(firehose_metrics: Dict[str, Any]) -> int:
    try:
        return int(firehose_metrics["Values"][0])
    except (IndexError, ValueError):
        logger.warning("Empty list or None value at end of list.")
        return 0
    except KeyError as err:
        logger.error("Expected 'Values', but dict was missing it")
        logger.error(err)
        raise
