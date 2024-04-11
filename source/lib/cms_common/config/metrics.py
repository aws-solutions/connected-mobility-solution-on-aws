# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from dataclasses import dataclass

# Connected Mobility Solution on AWS
from .ssm import (
    get_resolvable_ssm_deployment_uuid,
    get_resolvable_ssm_metrics_enabled,
    get_resolvable_ssm_metrics_url,
)


@dataclass(frozen=True)
class OperationalMetricsInput:
    metrics_url: str
    report_metrics_enabled: str
    deployment_uuid: str

    @classmethod
    def from_app_unique_id(cls, app_unique_id: str) -> "OperationalMetricsInput":
        return OperationalMetricsInput(
            metrics_url=get_resolvable_ssm_metrics_url(app_unique_id=app_unique_id),
            report_metrics_enabled=get_resolvable_ssm_metrics_enabled(
                app_unique_id=app_unique_id
            ),
            deployment_uuid=get_resolvable_ssm_deployment_uuid(
                app_unique_id=app_unique_id
            ),
        )
