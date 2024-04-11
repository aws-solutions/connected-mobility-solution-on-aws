# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import datetime
import os
from typing import Any, Dict

# Third Party Libraries
import requests

# AWS Libraries
from aws_lambda_powertools import Logger

logger = Logger()

METRICS_TIME_FORMAT = (
    "%Y-%m-%d %H:%M:%S.%f"  # Expected in this exact format by metrics API
)
REQUEST_TIMEOUT_SECONDS = 10


def write_metric(
    metric_data: Dict[str, Any],
) -> None:
    metric_post_data = {
        "Solution": os.environ["SOLUTION_ID"],
        "UUID": os.environ["DEPLOYMENT_UUID"],
        "TimeStamp": datetime.datetime.now().strftime(METRICS_TIME_FORMAT),
        "Version": os.environ["SOLUTION_VERSION"],
        "Data": metric_data,
    }

    requests.post(
        url=os.environ["METRICS_SOLUTION_URL"],
        json=metric_post_data,
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
