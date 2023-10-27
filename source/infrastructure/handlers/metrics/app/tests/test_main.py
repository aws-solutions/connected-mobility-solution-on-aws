# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import datetime
import os
from typing import Any, Dict
from unittest.mock import MagicMock, patch

# Third Party Libraries
import boto3
from freezegun import freeze_time

# Connected Mobility Solution on AWS
from ..lib import data_firehose_helper, metrics_publish, s3_helper
from ..main import build_config, lambda_handler
from . import UnitTestCommon

TEST_YEAR = 2023
TEST_MONTH = 1
TEST_DAY = 7
TEST_HOUR = 7
TEST_MINUTE = 0
TEST_SECOND = 0
TEST_TZ_OFFSET = -5


class TestHandler(UnitTestCommon):
    @freeze_time(
        f"{TEST_YEAR}-{TEST_MONTH}-{TEST_DAY} {TEST_HOUR}:{TEST_MINUTE}:{TEST_SECOND}",
        tz_offset=TEST_TZ_OFFSET,
    )
    @patch.object(metrics_publish, "write_metric")
    @patch.object(data_firehose_helper, "get_cms_data_firehose_utilization")
    @patch.object(s3_helper, "get_cms_s3_total_storage_in_use")
    @patch.object(boto3, "client")
    def test_get_metrics(
        self,
        mock_boto3_client: MagicMock,
        mock_get_cms_s3_total_storage_in_use: MagicMock,
        mock_get_cms_data_firehose_utilization: MagicMock,
        mock_write_metric: MagicMock,
    ) -> None:
        mock_get_cms_s3_total_storage_in_use.return_value = 1234
        mock_get_cms_data_firehose_utilization.return_value = {
            "total_put_requests_per_day": 5678,
            "total_num_data_streams_in_use_on_day": 1,
        }

        event: Dict[str, Any] = {}
        context: Dict[str, Any] = {}

        lambda_handler(event, context)

        self.assertEqual(mock_get_cms_s3_total_storage_in_use.call_count, 1)
        self.assertEqual(mock_get_cms_data_firehose_utilization.call_count, 1)
        self.assertEqual(mock_write_metric.call_count, 1)

        self.assertEqual(
            mock_get_cms_s3_total_storage_in_use.call_args[0][0],
            {
                "today": datetime.datetime(
                    TEST_YEAR, TEST_MONTH, TEST_DAY, 0, 0, tzinfo=datetime.timezone.utc
                ),
                "yesterday": datetime.datetime(
                    TEST_YEAR,
                    TEST_MONTH,
                    TEST_DAY - 1,
                    0,
                    0,
                    tzinfo=datetime.timezone.utc,
                ),
                "metric_timestamp": datetime.datetime(
                    TEST_YEAR,
                    TEST_MONTH,
                    TEST_DAY,
                    TEST_HOUR,
                    TEST_MINUTE,
                    TEST_SECOND,
                    0,
                )
                + datetime.timedelta(hours=TEST_TZ_OFFSET),
                "solution_id": os.environ["SOLUTION_ID"],
                "solution_version": os.environ["SOLUTION_VERSION"],
                "account_id": os.environ["AWS_ACCOUNT_ID"],
                "region": os.environ["AWS_REGION"],
                "metrics_solution_url": os.environ["METRICS_SOLUTION_URL"],
                "deployment_uuid": os.environ["DEPLOYMENT_UUID"],
            },
        )

    @freeze_time(
        f"{TEST_YEAR}-{TEST_MONTH}-{TEST_DAY} {TEST_HOUR}:{TEST_MINUTE}:{TEST_SECOND}",
        tz_offset=TEST_TZ_OFFSET,
    )
    def test_build_config(self) -> None:
        config = build_config()

        self.assertEqual(config["today"].day, datetime.datetime.utcnow().date().day)

        self.assertEqual(
            config["yesterday"].day, datetime.datetime.utcnow().date().day - 1
        )

        self.assertEqual(config["solution_id"], os.environ["SOLUTION_ID"])
        self.assertEqual(config["solution_version"], os.environ["SOLUTION_VERSION"])
        self.assertEqual(config["account_id"], os.environ["AWS_ACCOUNT_ID"])
        self.assertEqual(config["region"], os.environ["AWS_REGION"])
        self.assertEqual(
            config["metrics_solution_url"], os.environ["METRICS_SOLUTION_URL"]
        )
        self.assertEqual(config["deployment_uuid"], os.environ["DEPLOYMENT_UUID"])
