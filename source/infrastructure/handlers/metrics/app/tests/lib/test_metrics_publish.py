# -*- coding: utf-8 -*-

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from unittest.mock import MagicMock, patch

# Third Party Libraries
import requests

# Connected Mobility Solution on AWS
from ...lib import metrics_publish
from ...main import build_config
from .. import UnitTestCommon


class TestHandler(UnitTestCommon):
    @patch.object(requests, "post")
    def test_metrics_publisher(self, mock_requests_post: MagicMock) -> None:
        config = build_config()

        metric_timestamp = config["metric_timestamp"]
        formatted_timestamp = metric_timestamp.strftime(
            metrics_publish.METRICS_TIME_FORMAT
        )

        data = {"SomeMetric": "Test"}

        metric_data = {
            "Solution": config["solution_id"],
            "UUID": config["deployment_uuid"],
            "TimeStamp": formatted_timestamp,
            "Version": config["solution_version"],
            "Data": data,
        }

        metrics_publish.write_metric(config, data, metric_timestamp)

        mock_requests_post.assert_called_once()
        mock_requests_post.assert_called_with(
            url=config["metrics_solution_url"],
            json=metric_data,
            timeout=metrics_publish.REQUEST_TIMEOUT_SECONDS,
        )
