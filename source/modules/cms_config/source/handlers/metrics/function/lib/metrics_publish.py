# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import datetime
from typing import Any, Dict

# Third Party Libraries
import requests

# AWS Libraries
from aws_lambda_powertools import Tracer

tracer = Tracer()


METRICS_TIME_FORMAT = (
    "%Y-%m-%d %H:%M:%S.%f"  # Expected in this exact format by metrics API
)

REQUEST_TIMEOUT_SECONDS = 10


@tracer.capture_method()
def write_metric(
    config: Dict[str, Any],
    metric_data: Dict[str, Any],
    metric_timestamp: datetime.datetime,
) -> None:
    formatted_timestamp = metric_timestamp.strftime(METRICS_TIME_FORMAT)

    metric_post_data = {
        "Solution": config["solution_id"],
        "UUID": config["deployment_uuid"],
        "TimeStamp": formatted_timestamp,
        "Version": config["solution_version"],
        "Data": metric_data,
    }

    requests.post(
        url=config["metrics_solution_url"],
        json=metric_post_data,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
