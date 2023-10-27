# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
from dataclasses import dataclass


# pylint: disable=invalid-name
@dataclass(frozen=True)
class EVBatteryHealthConstantsClass:
    STAGE: str = os.environ.get("STAGE", "dev")
    APP_NAME: str = f"cms-ev-battery-health-on-aws-stack-{STAGE}"
    MODULE_NAME: str = "cms-ev-battery-health-on-aws"
    SOLUTION_NAME: str = "Connected Mobility Solution on AWS"
    SOLUTION_ID: str = "SO0241"
    SOLUTION_VERSION: str = "v1.0.0"
    APPLICATION_TYPE: str = "AWS-Solutions"
    CAPABILITY_ID = "CMS.11"
    USER_AGENT_STRING: str = f"AWSSOLUTION/{SOLUTION_ID}/{SOLUTION_VERSION} AWSSOLUTION-CAPABILITY/{CAPABILITY_ID}/{SOLUTION_VERSION}"

    DASHBOARD_S3_OBJECT_KEY_PREFIX: str = "cms/dashboards/"
    ALERTS_S3_OBJECT_KEY_PREFIX: str = "cms/alerts/"
    GRAFANA_API_KEY_EXPIRATION_DAYS: int = 30
    GRAFANA_ALERTS_SNS_TOPIC_NAME: str = f"grafana-alerts-{APP_NAME}"


EVBatteryHealthConstants = EVBatteryHealthConstantsClass()
