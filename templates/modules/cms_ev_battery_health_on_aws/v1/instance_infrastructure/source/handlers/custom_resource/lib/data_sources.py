# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from enum import Enum
from typing import Any, Dict


class GrafanaDataSourceType(Enum):
    ATHENA = "grafana-athena-datasource"


def construct_athena_data_source(properties: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "name": "Amazon Athena",
        "type": GrafanaDataSourceType.ATHENA.value,
        "access": "proxy",
        "url": None,
        "user": None,
        "database": None,
        "basicAuth": False,
        "isDefault": True,
        "jsonData": {
            "authType": "ec2_iam_role",
            "catalog": properties["catalog"],
            "database": properties["database"],
            "workgroup": properties["workgroup"],
            "defaultRegion": properties["defaultRegion"],
        },
    }
