# -*- coding: utf-8 -*-

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import dataclasses
from typing import Any, Callable, Dict

# Third Party Libraries
from grafanalib.core import Dashboard  # type: ignore

# Connected Mobility Solution on AWS
from .dashboards import create_ev_battery_health_dashboard


@dataclasses.dataclass(frozen=True)
class DashboardConfig:
    name: str
    s3_object_key_name: str
    dashboard_creator_func: Callable[[Dict[str, Any]], Dashboard]


DASHBOARD_CONFIGS = [
    DashboardConfig(
        name="EV Battery Health Dashboard",
        s3_object_key_name="ev_battery_health_dashboard",
        dashboard_creator_func=create_ev_battery_health_dashboard,
    ),
]
