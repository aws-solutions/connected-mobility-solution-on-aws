# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any, Dict, List, Union

# Third Party Libraries
from attr.validators import in_, instance_of
from attrs import define, field
from grafanalib.core import AlertCondition, AlertExpression  # type: ignore


@define(auto_attribs=True)
class AthenaTarget:
    # Adds support for Athena data sources and follows the pattern
    # from grafanalib.core.Target

    ref_id: str = field(kw_only=True, validator=instance_of(str))
    athena_sql_query: str = field(kw_only=True, validator=instance_of(str))
    glue_table_name: str = field(kw_only=True, validator=instance_of(str))
    datasource: str = field(kw_only=True, validator=instance_of(str))

    query_interval_ms: int = field(default=1000, validator=instance_of(int))
    max_number_of_query_results: int = field(default=10000, validator=instance_of(int))
    glue_catalog_name: str = field(default="__default", validator=instance_of(str))
    glue_database_name: str = field(default="__default", validator=instance_of(str))
    glue_region_name: str = field(default="__default", validator=instance_of(str))
    hide: bool = field(default=False, validator=instance_of(bool))

    def to_json_data(self) -> Dict[str, Any]:
        return {
            "connectionArgs": {
                "catalog": self.glue_catalog_name,
                "database": self.glue_database_name,
                "region": self.glue_region_name,
                "resultReuseEnabled": False,
                "resultReuseMaxAgeInMinutes": 60,
            },
            "format": 1,
            "hide": self.hide,
            "intervalMs": self.query_interval_ms,
            "maxDataPoints": self.max_number_of_query_results,
            "rawSQL": self.athena_sql_query,
            "refId": self.ref_id,
            "table": self.glue_table_name,
        }


@define(auto_attribs=True)
class GrafanaAlertRulev9:
    # Adds support for Grafana alerts with Athena data sources and follows
    # the pattern from grafanalib.core.AlertRulev9

    alert_title: str = field(kw_only=True, validator=instance_of(str))
    alert_evaluators: List[
        Union[AthenaTarget, AlertExpression, AlertCondition]
    ] = field(kw_only=True)

    annotations: Dict[str, Any] = field(factory=dict)
    labels: Dict[str, Any] = field(factory=dict)
    evaluation_time_period: str = field(default="5m", validator=instance_of(str))
    query_time_range_from_in_seconds: int = field(
        default=3600, validator=instance_of(int)
    )
    query_time_range_to_in_seconds: int = field(default=0, validator=instance_of(int))
    no_data_alert_state: str = field(
        default="NoData",
        validator=in_(
            [
                "OK",
                "NoData",
                "Alerting",
            ]
        ),
    )
    error_alert_state: str = field(
        default="Error",
        validator=in_(
            [
                "OK",
                "Alerting",
                "Error",
            ]
        ),
    )

    def to_json_data(self) -> Dict[str, Any]:
        alert_evaluators = []
        for alert_evaluator in self.alert_evaluators:
            if isinstance(alert_evaluator, AthenaTarget):
                alert_evaluators.append(
                    {
                        "refId": alert_evaluator.ref_id,
                        "relativeTimeRange": {
                            "from": self.query_time_range_from_in_seconds,
                            "to": self.query_time_range_to_in_seconds,
                        },
                        "datasourceUid": alert_evaluator.datasource,
                        "model": alert_evaluator.to_json_data(),
                    }
                )
            else:
                alert_evaluators.append(alert_evaluator.to_json_data())

        return {
            "annotations": self.annotations,
            "labels": self.labels,
            "for": self.evaluation_time_period,
            "grafana_alert": {
                "title": self.alert_title,
                "condition": "ALERT_CONDITION",
                "no_data_state": self.no_data_alert_state,
                "exec_err_state": self.error_alert_state,
                "is_paused": False,
                "data": alert_evaluators,
            },
        }
