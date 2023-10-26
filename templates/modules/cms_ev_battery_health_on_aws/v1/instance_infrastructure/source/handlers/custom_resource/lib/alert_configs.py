# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import dataclasses
from typing import Any, Callable, Dict

# Connected Mobility Solution on AWS
from .alerts import create_ev_battery_health_alert_rule_group


@dataclasses.dataclass(frozen=True)
class AlertGroupConfig:
    alert_group_folder: str
    s3_object_key_name: str
    alert_group_creator_func: Callable[[Dict[str, Any]], Dict[str, Any]]


ALERT_GROUP_CONFIGS = [
    AlertGroupConfig(
        alert_group_folder="ev_battery_health",
        s3_object_key_name="alert_rules",
        alert_group_creator_func=create_ev_battery_health_alert_rule_group,
    ),
]
