# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json
from typing import Any, Dict

# Third Party Libraries
from grafanalib._gen import DashboardEncoder  # type: ignore


def convert_grafanalib_alert_group_to_json_str(alert_group: Dict[str, Any]) -> str:
    return json.dumps(alert_group, sort_keys=True, indent=4, cls=DashboardEncoder)


def create_sns_alert_contact_point_payload(name: str, topic_arn: str) -> Dict[str, Any]:
    return {
        "type": "sns",
        "name": name,
        "settings": {
            "topic": topic_arn,
            "authProvider": "default",
            "messageFormat": "json",
        },
        "secureSettings": {},
    }


def create_alert_notification_policy_payload(receiver: str) -> Dict[str, Any]:
    return {
        "continue": False,
        "group_by": [],
        "object_matchers": [],
        "routes": [],
        "mute_time_intervals": [],
        "receiver": receiver,
    }
