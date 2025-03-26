# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json
import os
from typing import Any, Dict, List, Literal, TypedDict, Union

# Configuration
INPUT_DIR: str = "./routes/"  # Directory containing the original JSON files
OUTPUT_DIR: str = "./routes/"  # Directory to save the cleaned and minified JSON files

# Ensure the output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Define TypedDicts for structured JSON data


class LineStringGeometry(TypedDict):
    type: Literal["LineString"]
    coordinates: List[List[float]]  # List of [longitude, latitude]


class MultiLineStringGeometry(TypedDict):
    type: Literal["MultiLineString"]
    coordinates: List[List[List[float]]]  # List of list of [longitude, latitude]


GeometryType = Union[LineStringGeometry, MultiLineStringGeometry]


class Route(TypedDict):
    geometry: GeometryType


class Data(TypedDict):
    routes: List[Route]


class VehicleData(TypedDict, total=False):
    vehicleIndex: int
    warehouse: Dict[str, float]  # Assuming warehouse has latitude and longitude
    recordedEvents: List[
        Dict[str, Any]
    ]  # Define a specific TypedDict if structure is known
    data: Data


class CleanedGeometry(TypedDict):
    type: Literal["LineString", "MultiLineString"]
    coordinates: Any  # Retained as per the original geometry


class CleanedRoute(TypedDict):
    geometry: CleanedGeometry


class CleanedData(TypedDict):
    routes: List[CleanedRoute]


class CleanedVehicleData(TypedDict, total=False):
    vehicleIndex: int
    warehouse: Dict[str, float]
    recordedEvents: List[Dict[str, Any]]
    data: CleanedData


def clean_vehicle_json(vehicle_data: VehicleData) -> CleanedVehicleData:
    """
    Cleans the vehicle JSON data by retaining only the necessary fields and removing unused ones.

    Args:
        vehicle_data (VehicleData): The original vehicle JSON data.

    Returns:
        CleanedVehicleData: The cleaned vehicle JSON data.
    """
    cleaned_data: CleanedVehicleData = {}

    # Retain 'vehicleIndex' if it exists
    if "vehicleIndex" in vehicle_data:
        cleaned_data["vehicleIndex"] = vehicle_data["vehicleIndex"]

    # Retain 'warehouse' if it exists
    if "warehouse" in vehicle_data:
        cleaned_data["warehouse"] = vehicle_data["warehouse"]

    # Retain 'recordedEvents' if it exists
    if "recordedEvents" in vehicle_data:
        cleaned_data["recordedEvents"] = vehicle_data["recordedEvents"]

    # Process 'data' field
    if "data" in vehicle_data:
        data_field: Data = vehicle_data["data"]
        cleaned_data["data"] = {"routes": []}

        # Retain 'routes' within 'data'
        if "routes" in data_field:
            cleaned_data["data"]["routes"] = []
            for route in data_field["routes"]:
                if (
                    "geometry" in route
                    and "type" in route["geometry"]
                    and "coordinates" in route["geometry"]
                ):
                    # Ensure that 'geometry' is either LineString or MultiLineString
                    geom = route["geometry"]
                    if geom["type"] in ("LineString", "MultiLineString"):
                        cleaned_geometry: CleanedGeometry = {
                            "type": geom["type"],
                            "coordinates": geom["coordinates"],
                        }
                        cleaned_route: CleanedRoute = {"geometry": cleaned_geometry}
                        cleaned_data["data"]["routes"].append(cleaned_route)
        else:
            # If 'routes' is not present in 'data', set it to an empty list to satisfy TypedDict
            cleaned_data["data"]["routes"] = []

    return cleaned_data


def process_files() -> None:
    """
    Processes all JSON files in the INPUT_DIR by cleaning and minifying them,
    then saves the result to OUTPUT_DIR.
    """
    for filename in os.listdir(INPUT_DIR):
        if filename.endswith(".json"):
            input_path: str = os.path.join(INPUT_DIR, filename)
            output_path: str = os.path.join(OUTPUT_DIR, filename)

            try:
                with open(input_path, "r", encoding="utf-8") as infile:
                    vehicle_data: VehicleData = json.load(infile)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from {filename}: {e}")
                continue
            except Exception as e:
                print(f"Unexpected error reading {filename}: {e}")
                continue

            cleaned_data: CleanedVehicleData = clean_vehicle_json(vehicle_data)

            try:
                with open(output_path, "w", encoding="utf-8") as outfile:
                    # Minify JSON by removing whitespace
                    json.dump(cleaned_data, outfile, separators=(",", ":"))
                print(f"Processed and saved: {filename}")
            except Exception as e:
                print(f"Error writing cleaned data to {filename}: {e}")


if __name__ == "__main__":
    process_files()
