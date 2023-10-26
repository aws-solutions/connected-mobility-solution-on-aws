# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json
from typing import Any, Dict, Generator

# Third Party Libraries
import boto3
import pytest

# Connected Mobility Solution on AWS
from ...config.constants import EVBatteryHealthConstants


@pytest.fixture(name="s3_to_grafana_dashboard_event")
def fixture_s3_to_grafana_dashboard_event(
    s3_dashboard_bucket: str,
) -> Generator[Dict[str, Any], None, None]:
    s3_client = boto3.client("s3")

    dashboard_object_key = (
        EVBatteryHealthConstants.DASHBOARD_S3_OBJECT_KEY_PREFIX + "test-dashboard"
    )

    s3_client.put_object(
        Bucket=s3_dashboard_bucket,
        Key=dashboard_object_key,
        Body=json.dumps({}).encode("utf-8"),
    )

    yield {
        "Records": [
            {
                "s3": {
                    "bucket": {
                        "name": s3_dashboard_bucket,
                    },
                    "object": {
                        "key": dashboard_object_key,
                    },
                }
            }
        ]
    }


@pytest.fixture(name="s3_to_grafana_alerts_event")
def fixture_s3_to_grafana_alerts_event(
    s3_dashboard_bucket: str,
) -> Generator[Dict[str, Any], None, None]:
    s3_client = boto3.client("s3")

    alerts_object_key = (
        EVBatteryHealthConstants.ALERTS_S3_OBJECT_KEY_PREFIX
        + "test-folder/"
        + "test-dashboard"
    )

    s3_client.put_object(
        Bucket=s3_dashboard_bucket,
        Key=alerts_object_key,
        Body=json.dumps({}).encode("utf-8"),
    )

    yield {
        "Records": [
            {
                "s3": {
                    "bucket": {
                        "name": s3_dashboard_bucket,
                    },
                    "object": {
                        "key": alerts_object_key,
                    },
                }
            }
        ]
    }
