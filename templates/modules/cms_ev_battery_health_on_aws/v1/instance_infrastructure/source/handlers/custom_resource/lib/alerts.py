# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any, Dict

# Third Party Libraries
from grafanalib.core import (  # type: ignore
    EXP_REDUCER_FUNC_DROP_NN,
    EXP_REDUCER_FUNC_LAST,
    EXP_TYPE_MATH,
    EXP_TYPE_REDUCE,
    AlertExpression,
)

# Connected Mobility Solution on AWS
from .data_sources import GrafanaDataSourceType
from .grafana_abstractions import AthenaTarget, GrafanaAlertRulev9


def create_ev_battery_health_alert_rule_group(
    data_sources: Dict[str, Any],
) -> Dict[str, Any]:
    athena_data_source_uid = data_sources[GrafanaDataSourceType.ATHENA.value][
        "data_source"
    ]["uid"]
    athena_table_name = data_sources[GrafanaDataSourceType.ATHENA.value]["athena_table"]

    alert_rules = [
        GrafanaAlertRulev9(
            alert_title="Low Remaining Charge",
            alert_evaluators=[
                AthenaTarget(
                    ref_id="QUERY",
                    datasource=athena_data_source_uid,
                    athena_sql_query=(
                        "SELECT\n"  # nosec
                        "vehicleidentification.vin,\n"
                        'MIN(CAST(powertrain.tractionbattery.stateofcharge.current AS DOUBLE)*100.0) as "Remaining Charge (%)"\n'
                        f'FROM "{athena_table_name}"\n'
                        "WHERE $__timeFilter(currentlocation.timestamp, 'yyyy-MM-dd''T''HH:mm:ss.SSSSSS+00:00')\n"
                        "GROUP BY vehicleidentification.vin\n"
                    ),
                    glue_table_name=athena_table_name,
                ),
                AlertExpression(
                    refId="REDUCE_EXPRESSION",
                    expressionType=EXP_TYPE_REDUCE,
                    expression="QUERY",
                    reduceFunction=EXP_REDUCER_FUNC_LAST,
                    reduceMode=EXP_REDUCER_FUNC_DROP_NN,
                ),
                AlertExpression(
                    refId="ALERT_CONDITION",
                    expressionType=EXP_TYPE_MATH,
                    expression="$REDUCE_EXPRESSION < 25",
                ),
            ],
        ),
        GrafanaAlertRulev9(
            alert_title="Low Remaining Useful Life",
            alert_evaluators=[
                AthenaTarget(
                    ref_id="QUERY",
                    datasource=athena_data_source_uid,
                    athena_sql_query=(
                        "SELECT\n"  # nosec
                        "vehicleidentification.vin,\n"
                        'MIN(CAST(powertrain.tractionbattery.stateofhealth AS DOUBLE)*100.0) as "Remaining Useful Life (%)"\n'
                        f'FROM "{athena_table_name}"\n'
                        "WHERE $__timeFilter(currentlocation.timestamp, 'yyyy-MM-dd''T''HH:mm:ss.SSSSSS+00:00')\n"
                        "GROUP BY vehicleidentification.vin\n"
                    ),
                    glue_table_name=athena_table_name,
                ),
                AlertExpression(
                    refId="REDUCE_EXPRESSION",
                    expressionType=EXP_TYPE_REDUCE,
                    expression="QUERY",
                    reduceFunction=EXP_REDUCER_FUNC_LAST,
                    reduceMode=EXP_REDUCER_FUNC_DROP_NN,
                ),
                AlertExpression(
                    refId="ALERT_CONDITION",
                    expressionType=EXP_TYPE_MATH,
                    expression="$REDUCE_EXPRESSION < 82",
                ),
            ],
        ),
    ]

    return {
        "name": "EV Battery Health",
        "interval": "1m",
        "rules": alert_rules,
    }
