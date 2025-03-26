# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json
import os
from secrets import SystemRandom
from typing import Dict, List, Literal, Optional, Set, TypedDict, Union, cast

sr = SystemRandom()

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


class Route(TypedDict, total=False):
    geometry: GeometryType


class Data(TypedDict):
    routes: List[Route]


class RecordedEvent(TypedDict):
    latitude: float
    longitude: float
    title: str
    timestamp: int


class VehicleData(TypedDict, total=False):
    vehicleIndex: int
    warehouse: Dict[str, float]  # Assuming warehouse has 'latitude' and 'longitude'
    recordedEvents: List[RecordedEvent]
    data: Data


class CleanedGeometry(TypedDict):
    type: Literal["LineString", "MultiLineString"]
    coordinates: Union[
        List[List[float]], List[List[List[float]]]
    ]  # Retained as per original geometry


class CleanedRoute(TypedDict):
    geometry: CleanedGeometry


class CleanedData(TypedDict):
    routes: List[CleanedRoute]


class CleanedVehicleData(TypedDict, total=False):
    vehicleIndex: int
    warehouse: Dict[str, float]
    recordedEvents: List[RecordedEvent]
    data: CleanedData


def generate_hard_braking_events(
    route_data: VehicleData, num_events: int = 2
) -> List[RecordedEvent]:
    """
    Generate hard braking events aligned with the route's geometry coordinates.
    This version:
      - Collects coordinates only from the route-level geometry.
      - Ensures events are placed between 20% and 80% of the route length.
    """
    # Safely get all routes; return empty if none found
    routes: List[Route] = route_data.get("data", {}).get("routes", [])
    if not routes:
        return []

    # Collect all coordinates from the route-level geometry
    all_coords: List[List[float]] = []
    for r in routes:
        geometry: Optional[GeometryType] = r.get("geometry")
        if geometry is None:
            continue  # Skip if geometry is missing

        if geometry["type"] == "LineString":
            all_coords.extend(geometry["coordinates"])  # List[List[float]]
        elif geometry["type"] == "MultiLineString":
            for line in geometry["coordinates"]:  # line: List[List[float]]
                all_coords.extend(line)
        else:
            print(f"Unsupported geometry type: {geometry['type']}")

    total_points: int = len(all_coords)
    if total_points < 2:
        # Not enough points to place events
        return []

    # Calculate valid index range from 20% to 80%
    start_index: int = int(total_points * 0.2)
    end_index: int = int(total_points * 0.8)

    # If the route is very short, ensure we still have a valid range
    if end_index <= start_index:
        start_index = 1
        end_index = total_points - 2
        if start_index >= end_index:
            # Still invalid? The route is too short
            return []

    events: List[RecordedEvent] = []
    selected_indices: Set[int] = set()

    for _ in range(num_events):
        # Ensure unique event locations
        attempts: int = 0
        while attempts < 10:
            index: int = int(sr.uniform(start_index, end_index))
            if index not in selected_indices:
                selected_indices.add(index)
                break
            attempts += 1
        else:
            # If unable to find a unique index after several attempts, skip
            continue

        # GeoJSON standard is [longitude, latitude]
        lon, lat = all_coords[index]

        event: RecordedEvent = {
            "latitude": lat,
            "longitude": lon,
            "title": "Hard Braking",
            "timestamp": int(index / total_points * 100000),
        }
        events.append(event)

    return events


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
        # Initialize 'routes' to satisfy TypedDict
        cleaned_data["data"] = {"routes": []}

        # Retain 'routes' within 'data'
        if "routes" in data_field:
            for route in data_field["routes"]:
                if (
                    "geometry" in route
                    and "type" in route["geometry"]
                    and "coordinates" in route["geometry"]
                ):
                    # Ensure that 'geometry' is either LineString or MultiLineString
                    geom: GeometryType = cast(GeometryType, route["geometry"])
                    if geom["type"] in ("LineString", "MultiLineString"):
                        cleaned_geometry: CleanedGeometry = {
                            "type": geom["type"],
                            "coordinates": geom["coordinates"],
                        }
                        cleaned_route: CleanedRoute = {"geometry": cleaned_geometry}
                        cleaned_data["data"]["routes"].append(cleaned_route)

        # If 'routes' is not present, 'routes' key is already initialized as an empty list

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

            # Add hard braking events to the route
            recorded_events: List[RecordedEvent] = generate_hard_braking_events(
                vehicle_data, num_events=int(sr.uniform(2, 5))
            )
            vehicle_data["recordedEvents"] = recorded_events

            # Clean the vehicle JSON data
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
