# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List

# Connected Mobility Solution on AWS
from .validators import (
    validate_query_selection_string,
    validate_query_table_name,
    validate_query_vin_input,
)


@dataclass
class AthenaQuery:
    query_string_builder: Callable[[List[str], str, Dict[str, Any]], str]
    max_time_in_seconds: int
    multiple_results: bool


class QueryType(Enum):
    GET_VEHICLE = "getVehicle"
    LIST_VEHICLES = "listVehicles"


def get_selection_string(selection_set_list: List[str]) -> str:
    # Converts from array of values in the format of:
    #       selection/set/path/value
    # To a string of comma separated values of:
    #       "selection"."set"."path" as "selection.set.path"
    #
    # This is important for athena to interpret the selection statement correctly

    selection_strings = []
    for selection_path in selection_set_list:
        if selection_path.endswith("/value"):
            selection_path_as_list = selection_path[: -len("/value")].split("/")
            selection = ".".join([f'"{part}"' for part in selection_path_as_list])
            selection_label = ".".join(selection_path_as_list)
            selection_strings.append(f'{selection} as "{selection_label}"')
    return ", ".join(selection_strings)


# Query Builders
def build_get_vehicle_query(
    selection_set: List[str], glue_table: str, arguments: Dict[str, Any]
) -> str:
    selection_string = get_selection_string(selection_set)

    validate_query_selection_string(selection_string)
    validate_query_table_name(glue_table)
    validate_query_vin_input(arguments["vin"])

    query_string = f"SELECT {selection_string} FROM \"{glue_table}\" WHERE vehicleidentification.vin = '{arguments['vin']}' LIMIT 1"
    return query_string


def build_list_vehicles_query(
    selection_set: List[str], glue_table: str, arguments: Dict[str, Any]
) -> str:
    selection_string = get_selection_string(selection_set)
    row_limit = int(os.environ["RECORD_LIMIT"])
    row_offset = row_limit * int(arguments.get("page", 0))

    validate_query_selection_string(selection_string)
    validate_query_table_name(glue_table)

    query_string = f'SELECT {selection_string} FROM "{glue_table}" ORDER BY vehicleidentification.vin OFFSET {row_offset} LIMIT {row_limit}'
    return query_string


# Query Handlers
QUERY_TYPE_HANDLER: Dict[str, AthenaQuery] = {
    QueryType.GET_VEHICLE.value: AthenaQuery(
        query_string_builder=build_get_vehicle_query,
        max_time_in_seconds=30,
        multiple_results=False,
    ),
    QueryType.LIST_VEHICLES.value: AthenaQuery(
        query_string_builder=build_list_vehicles_query,
        max_time_in_seconds=60,
        multiple_results=True,
    ),
}
