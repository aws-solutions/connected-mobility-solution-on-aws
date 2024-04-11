# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from dataclasses import dataclass

# pylint: disable=invalid-name


@dataclass(frozen=True)
class CMSModuleShortNames:
    ALERTS: str = "alerts"
    API: str = "api"
    AUTH: str = "auth"
    CONFIG: str = "config"
    CONNECT_STORE: str = "connect-store"
    EV_BATTERY_HEALTH: str = "ev-battery-health"
    FLEETWISE_CONNECTOR: str = "fleetwise-connector"
    PROVISIONING: str = "provisioning"
    SAMPLE: str = "sample"
    VEHICLE_SIMULATOR: str = "vehicle-simulator"


# pylint: enable=invalid-name
