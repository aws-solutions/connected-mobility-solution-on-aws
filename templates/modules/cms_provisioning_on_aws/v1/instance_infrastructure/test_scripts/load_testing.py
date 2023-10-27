# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import multiprocessing
from enum import Enum
from typing import Callable, List

# Connected Mobility Solution on AWS
from .dynamodb_helpers import (
    add_vehicle_to_authorized_vehicles_table,
    create_random_authorized_vehicles,
    get_authorized_vehicles_table_name,
)
from .provisioning_by_claim import ProvisioningByClaim


class LoadTestType(Enum):
    SAME_VEHICLE = "same_vehicle"
    MULTIPLE_VEHICLE = "multiple_vehicle"


def provisioning_by_claim(vin: str) -> None:
    provisioning = ProvisioningByClaim(vin=vin)
    provisioning.send_vehicle_provisioning_request()


def run(test_func: Callable[[str], None], vins: List[str]) -> None:
    # Use multiprocessing to run the test function n times
    with multiprocessing.Pool() as pool:
        pool.map(test_func, vins)
        pool.close()
        pool.join()


def load_test_same_vehicle(num_vehicles: int) -> None:
    vehicle_vin = "KMHFG4JG1CA181127"
    add_vehicle_to_authorized_vehicles_table(
        vin=vehicle_vin,
        table_name=get_authorized_vehicles_table_name(),
    )
    vins = [vehicle_vin] * num_vehicles
    run(test_func=provisioning_by_claim, vins=vins)
    print("Done")


def load_test_multiple_vehicle(num_vehicles: int) -> None:
    vins = create_random_authorized_vehicles(num_vehicles)
    run(test_func=provisioning_by_claim, vins=vins)
    print("Done")


if __name__ == "__main__":
    # configure load test
    NUM_VEHICLES = 100
    TEST_TYPE = LoadTestType.SAME_VEHICLE

    # run load test
    if TEST_TYPE is LoadTestType.SAME_VEHICLE:
        # load test provisioning same vehicle
        load_test_same_vehicle(num_vehicles=NUM_VEHICLES)
    elif TEST_TYPE is LoadTestType.MULTIPLE_VEHICLE:
        # load test provisioning multiple vehicles
        load_test_multiple_vehicle(num_vehicles=NUM_VEHICLES)
