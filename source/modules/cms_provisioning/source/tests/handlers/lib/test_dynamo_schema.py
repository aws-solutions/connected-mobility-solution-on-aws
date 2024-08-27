# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any, Dict

# Third Party Libraries
import pytest

# Connected Mobility Solution on AWS
from ....handlers.provisioning.function.lib.dynamo_schema import (
    AuthorizedVehicle,
    from_ddb_item,
)


def test_type_validation_fails_with_missing_args() -> None:
    # need to specify all arguments
    with pytest.raises(Exception):
        AuthorizedVehicle()  # type: ignore # pylint: disable=no-value-for-parameter


def test_type_validation_fails_with_incorrect_type() -> None:
    # initialize dataclass with inappropriate allow_provisioning type
    # allow_provisioning should be bool
    with pytest.raises(Exception):
        AuthorizedVehicle(
            vin="ABCD",
            make="make",
            model="model",
            year="year",
            allow_provisioning="False",  # type: ignore
        )


def test_type_validation_succeeds() -> None:
    # initialize dataclass with appropriate types
    vehicle = AuthorizedVehicle(
        vin="ABCD",
        make="make",
        model="model",
        year="year",
        allow_provisioning=False,
    )
    assert isinstance(vehicle, AuthorizedVehicle)


def test_construct_from_ddb_item() -> None:
    ddb_item: Dict[str, Any] = {
        "vin": {"S": "ABCD"},
        "make": {"S": "make"},
        "model": {"S": "model"},
        "year": {"S": "year"},
        "allow_provisioning": {"BOOL": True},
    }
    vehicle: AuthorizedVehicle = from_ddb_item(AuthorizedVehicle, ddb_item)

    assert vehicle.vin == ddb_item["vin"]["S"]
    assert vehicle.make == ddb_item["make"]["S"]
    assert vehicle.model == ddb_item["model"]["S"]
    assert vehicle.year == ddb_item["year"]["S"]
    assert vehicle.allow_provisioning == ddb_item["allow_provisioning"]["BOOL"]
