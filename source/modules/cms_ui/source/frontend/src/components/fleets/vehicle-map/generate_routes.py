# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

# Standard Library
import json
import os
import time
from secrets import SystemRandom
from typing import Any, Dict, List

# Third Party Libraries
import requests

NUMBER_OF_VEHICLES: int = 100
NUMBER_FROM_A: int = 50
NUMBER_FROM_B: int = 50
NUM_STOPS_PER_ROUTE: int = 10

Coordinate = Dict[str, float]

warehouseA: Coordinate = {"latitude": 36.266964, "longitude": -115.0415586}
warehouseB: Coordinate = {"latitude": 36.045379, "longitude": -115.187102}

LAT_MIN: float = 36.101174
LAT_MAX: float = 36.241411
LON_MIN: float = -115.287594
LON_MAX: float = -115.092244

OUTPUT_DIR: str = "./routes/"
os.makedirs(OUTPUT_DIR, exist_ok=True)

sr = SystemRandom()


def generate_random_stops(num_stops: int = 10) -> List[Coordinate]:
    stops: List[Coordinate] = []
    for _ in range(num_stops):
        lat: float = sr.uniform(LAT_MIN, LAT_MAX)
        lon: float = sr.uniform(LON_MIN, LON_MAX)
        stops.append({"latitude": lat, "longitude": lon})
    return stops


def construct_route_url(warehouse: Coordinate, stops: List[Coordinate]) -> str:
    coords = [
        f"{warehouse['longitude']},{warehouse['latitude']}",
        *[f"{s['longitude']},{s['latitude']}" for s in stops],
        f"{warehouse['longitude']},{warehouse['latitude']}",
    ]
    route_url = (
        "http://router.project-osrm.org/route/v1/driving/"
        + ";".join(coords)
        + "?overview=full&geometries=geojson&steps=true"
    )
    return route_url


def main() -> None:
    for i in range(NUMBER_OF_VEHICLES):
        warehouse: Coordinate = warehouseA if i < NUMBER_FROM_A else warehouseB
        stops: List[Coordinate] = generate_random_stops(NUM_STOPS_PER_ROUTE)
        route_url: str = construct_route_url(warehouse, stops)

        print(f"Fetching route for vehicle {i}...")
        response = requests.get(route_url, timeout=10)  # Add a timeout
        if response.status_code == 200:
            data: Any = response.json()

            route_data = {
                "vehicleIndex": i,
                "warehouse": warehouse,
                "stops": stops,
                "data": data,
            }

            output_file = os.path.join(OUTPUT_DIR, f"vehicle_{i}.json")
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(route_data, f, separators=(",", ":"))
            print(f"Fetched route for vehicle {i}, saved to {output_file}.")
        else:
            print(
                f"Failed to fetch route for vehicle {i}, status: {response.status_code}"
            )

        time.sleep(1)


if __name__ == "__main__":
    main()
