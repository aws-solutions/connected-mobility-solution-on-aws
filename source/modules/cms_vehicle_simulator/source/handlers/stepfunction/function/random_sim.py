# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import math
import random
import string
from typing import Any, Dict, Tuple
from uuid import uuid4

# Third Party Libraries
import arrow


class GenericSim:
    @staticmethod
    def generic_sim_id(limits: Dict[str, Any], counter: int = 0) -> str:
        return str(uuid4())

    @staticmethod
    def generic_sim_bool(limits: Dict[str, Any], counter: int = 0) -> bool:
        return random.choice([True, False])  # nosec  # NOSONAR

    @staticmethod
    def generic_sim_decay(limits: Dict[str, Any], counter: int = 0) -> float:
        return int(limits.get("max", 100)) - (
            (int(limits.get("max", 100)) - int(limits.get("min", 0)))
            * (1 - math.exp(-0.05 * counter))
        )

    @staticmethod
    def generic_sim_float(limits: Dict[str, Any], counter: int = 0) -> float:
        return round(
            random.random(), int(limits.get("precision", 4))  # nosec  # NOSONAR
        )

    @staticmethod
    def generic_sim_int(limits: Dict[str, Any], counter: int = 0) -> int:
        return random.randint(  # nosec  # NOSONAR
            int(limits.get("min", 0)), int(limits.get("max", 100000))
        )

    @staticmethod
    def generic_sim_location(
        limits: Dict[str, Any], counter: int = 0
    ) -> Dict[str, float]:
        def get_random_lat_lng() -> Tuple[float, float]:
            # radians to degrees Correction Factor
            correction_factor = 180.0 / math.pi
            # angle with Equator   - from +pi/2 to -pi/2
            rad_lat = math.asin(2 * random.uniform(0.0, 1.0) - 1.0)  # nosec  # NOSONAR
            # longitude in radians - from -pi to +pi
            rad_lon = (2 * random.uniform(0.0, 1.0) - 1) * math.pi  # nosec  # NOSONAR
            return (
                round(rad_lat * correction_factor, 5),
                round(rad_lon * correction_factor, 5),
            )

        dec_lat = random.random() / 100  # nosec  # NOSONAR
        dec_lon = random.random() / 100  # nosec  # NOSONAR

        if not limits["lat"] or not limits["long"]:
            lat, lon = get_random_lat_lng()
        else:
            lat = limits["lat"]
            lon = limits["long"]

        return {
            "latitude": lat + dec_lat,
            "longitude": lon + dec_lon,
        }

    @staticmethod
    def generic_sim_object(limits: Dict[str, Any], counter: int = 0) -> Dict[str, Any]:
        sim_object = {}
        for field in limits["payload"]:
            sim_object[field["name"]] = getattr(
                GenericSim, f"generic_sim_{field['type']}"
            )(field)

        return sim_object

    @staticmethod
    def generic_sim_string(limits: Dict[str, Any], counter: int = 0) -> str:
        if limits.get("static"):
            return str(limits.get("default", "static"))

        # This field is to generate random data, there is no security implication
        return "".join(
            random.choices(  # nosec # NOSONAR
                string.ascii_letters,
                k=random.randint(  # NOSONAR
                    int(limits.get("min", 0)), int(limits.get("max", 20))
                ),  # nosec
            )
        )

    @staticmethod
    def generic_sim_sinusoidal(limits: Dict[str, Any], counter: int = 0) -> float:
        step = 0.087266527777778
        return (math.sin(step * counter) + int(limits.get("min", -1)) + 1) * (
            int(limits.get("max", 1)) / 2
        )

    @staticmethod
    def generic_sim_timestamp(limits: Dict[str, Any], counter: int = 0) -> str:
        return arrow.utcnow().isoformat()

    @staticmethod
    def generic_sim_pickOne(  # pylint: disable=invalid-name # NOSONAR
        limits: Dict[str, Any], counter: int = 0
    ) -> Any:
        # This field is to generate random data, there is no security implication
        return random.choice(limits.get("arr", [1, 2, 3, 4, 5]))  # nosec  # NOSONAR
