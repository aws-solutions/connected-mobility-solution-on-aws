# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import datetime
import os
import unittest
from typing import Any, Dict, List

__all__: List[Any] = []


class UnitTestCommon(unittest.TestCase):
    def setUp(self) -> None:
        set_common_env_variables()
        return super().setUp()


def set_common_env_variables() -> None:
    os.environ["SOLUTION_ID"] = "SO0241"
    os.environ["SOLUTION_VERSION"] = "v1.0.2"
    os.environ["AWS_ACCOUNT_ID"] = "0123456789123"
    os.environ["AWS_REGION"] = "us-east-1"
    os.environ["DEPLOYMENT_UUID"] = "DUMMY"
    os.environ["METRICS_SOLUTION_URL"] = "https://localhost"
    os.environ["USER_AGENT_STRING"] = "USER_AGENT"


def get_solution_resource_tags(
    solution_id: str, deployment_uuid: str, module_name: str
) -> List[Dict[str, Any]]:
    return [
        {"Key": "Solutions:SolutionID", "Value": solution_id},
        {
            "Key": "Solutions:ModuleName",
            "Value": module_name,
        },
        {"Key": "Solutions:DeploymentUUID", "Value": deployment_uuid},
        {"Key": "Solutions:SolutionVersion", "Value": "v1.0.2"},
        {"Key": "Solutions:ApplicationType", "Value": "AWS-Solutions"},
        {
            "Key": "Solutions:SolutionName",
            "Value": "Connected Mobility Solution on AWS",
        },
    ]


def get_halfway_yesterday_time_utc() -> datetime.datetime:
    utc_today = datetime.datetime.utcnow().date()
    utc_today_time = datetime.datetime(
        utc_today.year,
        utc_today.month,
        utc_today.day,
        0,
        0,
        0,
        0,
        datetime.timezone.utc,
    )
    return utc_today_time - datetime.timedelta(hours=12)
