# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0


# Standard Library
# mypy: disable-error-code=misc
import re
from datetime import datetime
from typing import Any, Dict
from unittest.mock import MagicMock

# Third Party Libraries
from moto import mock_aws

# AWS Libraries
from aws_lambda_powertools.utilities.typing import LambdaContext

# Connected Mobility Solution on AWS
from ....handlers.stepfunction.function.handlers import data_sim_handler
from ....handlers.stepfunction.function.random_sim import GenericSim

MAX_LAT = 90
MIN_LAT = -90
MAX_LON = 180
MIN_LON = -180


@mock_aws
def test_lambda_handler(
    simulate_data_event: Dict[str, Any], context: LambdaContext, mocker: MagicMock
) -> None:
    mocked_iot: MagicMock = mocker.patch("botocore.client.BaseClient._make_api_call")

    data_sim_handler(simulate_data_event, context)
    mocked_iot.assert_called()


def test_generic_sim_id(limits: Dict[str, Any]) -> None:
    sim_uuid = GenericSim.generic_sim_id(limits)
    re.match("[0-9a-f]{12}4[0-9a-f]{3}[89ab][0-9a-f]{15}$", sim_uuid)


def test_generic_sim_bool(limits: Dict[str, Any]) -> None:
    sim_bool = GenericSim.generic_sim_bool(limits)
    assert isinstance(sim_bool, bool)


def test_generic_sim_decay(limits: Dict[str, Any]) -> None:
    sim_decay = GenericSim.generic_sim_decay(limits, counter=0)
    assert sim_decay == limits["max"]

    sim_decay = GenericSim.generic_sim_decay(limits, counter=10000)
    assert sim_decay < limits["max"]


def test_generic_sim_float(limits: Dict[str, Any]) -> None:
    sim_float = GenericSim.generic_sim_float(limits)
    assert isinstance(sim_float, float)

    decimal = str(sim_float).split(".")[1]
    assert len(decimal) <= limits["precision"]


def test_generic_sim_int(limits: Dict[str, Any]) -> None:
    sim_int = GenericSim.generic_sim_int(limits)
    assert isinstance(sim_int, int)
    assert limits["min"] <= sim_int <= limits["max"]


def test_generic_sim_location(limits: Dict[str, Any]) -> None:
    sim_coordinates = GenericSim.generic_sim_location(limits)
    lat = sim_coordinates["latitude"]
    lon = sim_coordinates["longitude"]

    assert isinstance(lat, float)
    assert isinstance(lon, float)
    assert MIN_LAT <= lat <= MAX_LAT
    assert MIN_LON <= lon <= MAX_LON


def test_generic_sim_object(limits: Dict[str, Any]) -> None:
    sim_object = GenericSim.generic_sim_object(limits)
    sim_object_keys = sim_object.keys()
    payload_field_names = {field["name"] for field in limits["payload"]}
    assert sim_object_keys == payload_field_names


def test_generic_sim_string(limits: Dict[str, Any]) -> None:
    sim_string = GenericSim.generic_sim_string(limits)
    assert re.match("^[a-zA-Z]+$", sim_string)
    assert limits["min"] <= len(sim_string) <= limits["max"]


def test_generic_sim_sinusoidal(limits: Dict[str, Any]) -> None:
    sim_sinusoidal = GenericSim.generic_sim_sinusoidal(limits)
    assert limits["min"] <= sim_sinusoidal <= limits["max"]


def test_generic_sim_timestamp(limits: Dict[str, Any]) -> None:
    sim_timestamp = GenericSim.generic_sim_timestamp(limits)
    iso_format = "%Y-%m-%dT%H:%M:%S.%f%z"
    assert datetime.strptime(sim_timestamp, iso_format)


def test_generic_sim_pickOne(  # pylint: disable=invalid-name
    limits: Dict[str, Any]
) -> None:
    sim_choice = GenericSim.generic_sim_pickOne(limits)
    assert sim_choice in limits["arr"]
