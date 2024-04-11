# -*- coding: utf-8 -*-

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json

# Third Party Libraries
from grafanalib._gen import DashboardEncoder  # type: ignore
from grafanalib.core import Dashboard  # type: ignore


def convert_grafanalib_dashboard_to_json_str(
    dashboard: Dashboard, overwrite: bool = False, message: str = ""
) -> str:
    # convert the grafanalib abstracted Dashboard object to formatted json
    # str object in the schema that is acceptable by the grafana api to
    # create a new dashboard.
    return json.dumps(
        {
            "dashboard": dashboard.to_json_data(),
            "overwrite": overwrite,
            "message": message,
        },
        sort_keys=True,
        indent=2,
        cls=DashboardEncoder,
    )
