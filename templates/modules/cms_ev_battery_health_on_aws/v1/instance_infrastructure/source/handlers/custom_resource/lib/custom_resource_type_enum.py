# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from enum import Enum


class CustomResourceType:
    class RequestType(Enum):
        CREATE = "Create"
        UPDATE = "Update"
        DELETE = "Delete"

    class ResourceType(Enum):
        CREATE_GRAFANA_API_KEY = "CreateGrafanaApiKey"
        CREATE_GRAFANA_DATA_SOURCE = "CreateGrafanaDataSource"
        CREATE_GRAFANA_DASHBOARD_AND_UPLOAD_TO_S3 = (
            "CreateGrafanaDashboardAndUploadToS3"
        )
        ENABLE_GRAFANA_ALERTING = "EnableGrafanaAlerting"
        SET_GRAFANA_ALERT_CONFIGURATION = "SetGrafanaAlertConfiguration"
        CREATE_GRAFANA_ALERTS_AND_UPLOAD_TO_S3 = "CreateGrafanaAlertsAndUploadToS3"

    class StatusType(Enum):
        SUCCESS = "SUCCESS"
        FAILED = "FAILED"
