# -*- coding: utf-8 -*-

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import re
from typing import Any, Dict

# Third Party Libraries
from grafanalib.core import (  # type: ignore
    GAUGE_CALC_LAST,
    Dashboard,
    GaugePanel,
    GridPos,
    RowPanel,
    Stat,
    Templating,
    Text,
    TimeSeries,
)

# Connected Mobility Solution on AWS
from .data_sources import GrafanaDataSourceType


def create_ev_battery_health_dashboard(data_sources: Dict[str, Any]) -> Dashboard:
    # extract the required data sources from the list of data sources
    athena_data_source = {
        "type": data_sources[GrafanaDataSourceType.ATHENA.value]["data_source"]["type"],
        "uid": data_sources[GrafanaDataSourceType.ATHENA.value]["data_source"]["uid"],
    }
    athena_table = data_sources[GrafanaDataSourceType.ATHENA.value]["athena_table"]
    # verify that the athena table name does not have sql injection vectors
    hyphenated_words_pattern = re.compile(r"[A-Za-z0-9-]+")

    # Checks whether the whole string matches the re.pattern or not
    if not re.fullmatch(hyphenated_words_pattern, athena_table):
        raise ValueError(
            f"Athena table name is not valid: {athena_table} should only consist of alphabets, numbers and hyphens!"
        )

    return Dashboard(
        title="EV Battery Health Dashboard",
        description="Dashboard to monitor the health of EV battery.",
        timezone="browser",
        panels=[
            RowPanel(gridPos=GridPos(h=1, w=24, x=0, y=0), collapsed=False),
            Text(
                gridPos=GridPos(h=2, w=5, x=0, y=1),
                content="## <strong>EV Battery Health Dashboard</strong>",
                transparent=True,
            ),
            RowPanel(collapsed=False, gridPos=GridPos(h=1, w=24, x=0, y=3)),
            Stat(
                gridPos=GridPos(h=6, w=4, x=0, y=17),
                dataSource=athena_data_source,
                noValue="0",
                reduceCalc="lastNotNull",
                thresholdType="percentage",
                thresholds=[
                    {"color": "green", "value": None},
                    {"color": "red", "value": 80},
                ],
                transparent=True,
                targets=[
                    {
                        "connectionArgs": {
                            "catalog": "__default",
                            "database": "__default",
                            "region": "__default",
                            "resultReuseEnabled": False,
                            "resultReuseMaxAgeInMinutes": 60,
                        },
                        "datasource": athena_data_source,
                        "format": 1,
                        "rawSQL": (
                            "SELECT\n"  # nosec
                            'CAST(powertrain.range AS DOUBLE)*1.6/1000.0 as "Range - Hybrid Sources (mi)",\n'
                            "date_parse(SUBSTRING(currentlocation.timestamp, 1, 19), '%Y-%m-%dT%H:%i:%s') AS time_stamp\n"
                            f'FROM "{athena_table}"\n'
                            "WHERE vehicleidentification.vin = '${vin:raw}'"
                            "ORDER BY time_stamp DESC\n"
                            "LIMIT 1\n"
                        ),
                        "refId": "A",
                    }
                ],
            ),
            Stat(
                gridPos=GridPos(h=6, w=4, x=0, y=11),
                dataSource=athena_data_source,
                noValue="0",
                reduceCalc="lastNotNull",
                thresholdType="percentage",
                thresholds=[
                    {"color": "green", "value": None},
                    {"color": "red", "value": 80},
                ],
                transparent=True,
                targets=[
                    {
                        "connectionArgs": {
                            "catalog": "__default",
                            "database": "__default",
                            "region": "__default",
                            "resultReuseEnabled": False,
                            "resultReuseMaxAgeInMinutes": 60,
                        },
                        "datasource": athena_data_source,
                        "format": 1,
                        "rawSQL": (
                            "SELECT\n"  # nosec
                            'CAST(powertrain.tractionbattery.range AS DOUBLE)*1.6/1000.0 as "Range - Battery (mi)",\n'
                            "date_parse(SUBSTRING(currentlocation.timestamp, 1, 19), '%Y-%m-%dT%H:%i:%s') AS time_stamp\n"
                            f'FROM "{athena_table}"\n'
                            "WHERE vehicleidentification.vin = '${vin:raw}'"
                            "ORDER BY time_stamp DESC\n"
                            "LIMIT 1\n"
                        ),
                        "refId": "A",
                    }
                ],
            ),
            GaugePanel(
                gridPos=GridPos(h=7, w=5, x=0, y=4),
                dataSource=athena_data_source,
                thresholdType="percentage",
                thresholds=[
                    {"color": "red", "value": None},
                    {"color": "green", "value": 30},
                ],
                calc=GAUGE_CALC_LAST,
                thresholdMarkers=True,
                targets=[
                    {
                        "connectionArgs": {
                            "catalog": "__default",
                            "database": "__default",
                            "region": "__default",
                            "resultReuseEnabled": False,
                            "resultReuseMaxAgeInMinutes": 60,
                        },
                        "datasource": athena_data_source,
                        "format": 1,
                        "rawSQL": (
                            "SELECT\n"  # nosec
                            'CAST(powertrain.tractionbattery.stateofcharge.current AS DOUBLE)*100.0 as "Remaining Charge (%)",\n'
                            "date_parse(SUBSTRING(currentlocation.timestamp, 1, 19), '%Y-%m-%dT%H:%i:%s') AS time_stamp\n"
                            f'FROM "{athena_table}"\n'
                            "WHERE vehicleidentification.vin = '${vin:raw}'"
                            "ORDER BY time_stamp DESC\n"
                            "LIMIT 1\n"
                        ),
                        "refId": "A",
                    }
                ],
                transparent=True,
                label="Remaining Charge (%)",
            ),
            GaugePanel(
                gridPos=GridPos(h=7, w=5, x=5, y=4),
                dataSource=athena_data_source,
                thresholdType="percentage",
                thresholds=[
                    {"color": "red", "value": None},
                    {"color": "green", "value": 50},
                ],
                calc=GAUGE_CALC_LAST,
                thresholdMarkers=True,
                targets=[
                    {
                        "connectionArgs": {
                            "catalog": "__default",
                            "database": "__default",
                            "region": "__default",
                            "resultReuseEnabled": False,
                            "resultReuseMaxAgeInMinutes": 60,
                        },
                        "datasource": athena_data_source,
                        "format": 1,
                        "rawSQL": (
                            "SELECT\n"  # nosec
                            'CAST(powertrain.tractionbattery.stateofhealth AS DOUBLE)*100.0 as "Remaining Useful Life (%)",\n'
                            "date_parse(SUBSTRING(currentlocation.timestamp, 1, 19), '%Y-%m-%dT%H:%i:%s') AS time_stamp\n"
                            f'FROM "{athena_table}"\n'
                            "WHERE vehicleidentification.vin = '${vin:raw}'"
                            "ORDER BY time_stamp DESC\n"
                            "LIMIT 1\n"
                        ),
                        "refId": "A",
                    }
                ],
                transparent=True,
                label="Remaining Useful Life (%)",
            ),
            TimeSeries(
                gridPos=GridPos(h=12, w=16, x=4, y=11),
                dataSource=athena_data_source,
                targets=[
                    {
                        "connectionArgs": {
                            "catalog": "__default",
                            "database": "__default",
                            "region": "__default",
                            "resultReuseEnabled": False,
                            "resultReuseMaxAgeInMinutes": 60,
                        },
                        "datasource": athena_data_source,
                        "format": 1,
                        "rawSQL": (
                            "SELECT\n"  # nosec
                            "date_parse(SUBSTRING(currentlocation.timestamp, 1, 19), '%Y-%m-%dT%H:%i:%s') AS time_stamp,\n"
                            'CAST(powertrain.tractionbattery.stateofhealth AS DOUBLE)*100.0 as "Remaining Useful Life (%)"\n'
                            f'FROM "{athena_table}"\n'
                            "WHERE vehicleidentification.vin = '${vin:raw}'"
                            "ORDER BY time_stamp"
                        ),
                        "refId": "A",
                    }
                ],
                axisLabel="Remaining Useful Life (%)",
                thresholdType="percentage",
                legendPlacement="right",
                transparent=True,
            ),
            GaugePanel(
                gridPos=GridPos(h=7, w=5, x=10, y=4),
                dataSource=athena_data_source,
                thresholdType="percentage",
                thresholds=[
                    {"color": "green", "value": None},
                    {"color": "red", "value": 80},
                ],
                calc=GAUGE_CALC_LAST,
                thresholdMarkers=True,
                targets=[
                    {
                        "connectionArgs": {
                            "catalog": "__default",
                            "database": "__default",
                            "region": "__default",
                            "resultReuseEnabled": False,
                            "resultReuseMaxAgeInMinutes": 60,
                        },
                        "datasource": athena_data_source,
                        "format": 1,
                        "rawSQL": (
                            "SELECT\n"  # nosec
                            "CAST(powertrain.tractionbattery.temperature.average AS DOUBLE)*100.0 as temperature,\n"
                            "date_parse(SUBSTRING(currentlocation.timestamp, 1, 19), '%Y-%m-%dT%H:%i:%s') AS time_stamp\n"
                            f'FROM "{athena_table}"\n'
                            "WHERE vehicleidentification.vin = '${vin:raw}'"
                            "ORDER BY time_stamp DESC\n"
                            "LIMIT 1\n"
                        ),
                        "refId": "A",
                    }
                ],
                transparent=True,
                label="Average Temperature (C)",
            ),
            GaugePanel(
                gridPos=GridPos(h=7, w=5, x=15, y=4),
                dataSource=athena_data_source,
                thresholdType="percentage",
                thresholds=[
                    {"color": "green", "value": None},
                    {"color": "red", "value": 80},
                ],
                calc=GAUGE_CALC_LAST,
                thresholdMarkers=True,
                targets=[
                    {
                        "connectionArgs": {
                            "catalog": "__default",
                            "database": "__default",
                            "region": "__default",
                            "resultReuseEnabled": False,
                            "resultReuseMaxAgeInMinutes": 60,
                        },
                        "datasource": athena_data_source,
                        "format": 1,
                        "rawSQL": (
                            "SELECT\n"  # nosec
                            "CAST(powertrain.tractionbattery.currentvoltage AS DOUBLE)*100 as voltage,\n"
                            "date_parse(SUBSTRING(currentlocation.timestamp, 1, 19), '%Y-%m-%dT%H:%i:%s') AS time_stamp\n"
                            f'FROM "{athena_table}"\n'
                            "WHERE vehicleidentification.vin = '${vin:raw}'"
                            "ORDER BY time_stamp DESC\n"
                            "LIMIT 1\n"
                        ),
                        "refId": "A",
                    }
                ],
                transparent=True,
                label="Current Voltage (V)",
            ),
            RowPanel(collapsed=False, gridPos=GridPos(h=1, w=24, x=0, y=23)),
        ],
        templating=Templating(
            list=[
                {
                    "name": "vin",
                    "label": "VIN",
                    "current": {
                        "selected": False,
                        "text": None,
                        "value": None,
                    },
                    "description": "Vehicle Identification Numbers",
                    "includeAll": False,
                    "multi": False,
                    "options": [],
                    "type": "query",
                    "query": {
                        "connectionArgs": {
                            "catalog": "__default",
                            "database": "__default",
                            "region": "__default",
                            "resultReuseEnabled": False,
                            "resultReuseMaxAgeInMinutes": 60,
                        },
                        "format": 1,
                        "rawSQL": 'SELECT DISTINCT vehicleidentification.vin as vin FROM "iot-main-stream-glue-schema-table"',
                        "table": "iot-main-stream-glue-schema-table",
                    },
                    "refresh": 1,
                }
            ],
        ),
    ).auto_panel_ids()
