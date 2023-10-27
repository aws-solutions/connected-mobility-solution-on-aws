# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json
import os
from typing import Any, Dict, Generator
from unittest import mock

# Third Party Libraries
import pytest
from chalice.app import Request

# Connected Mobility Solution on AWS
from ....config.constants import VSConstants


@pytest.fixture(autouse=True, scope="session")
def fixture_env_vars() -> Generator[None, None, None]:
    env_vars = {
        "DYN_DEVICE_TYPES_TABLE": "test",
        "DYN_SIMULATIONS_TABLE": "test",
        "DYN_TEMPLATES_TABLE": "test",
        "CROSS_ORIGIN_DOMAIN": "test",
        "USER_POOL_ARN": "test",
        "SIMULATOR_STATE_MACHINE_NAME": "test",
        "USER_AGENT_STRING": VSConstants.USER_AGENT_STRING,
    }
    with mock.patch.dict(os.environ, env_vars):
        yield


@pytest.fixture(name="vsapi_basic_event")
def fixture_create_event() -> Dict[str, Any]:
    return {
        "multiValueQueryStringParameters": {},
        "headers": {"content-type": "application/json"},
        "pathParameters": None,
        "isBase64Encoded": False,
        "body": json.dumps({"test": "test"}),
        "requestContext": {
            "resourcePath": "",
            "httpMethod": "GET",
        },
        "stageVariables": None,
    }


@pytest.fixture(name="vsapi_create_template_event")
def fixture_create_template_event(vsapi_basic_event: Dict[str, Any]) -> Request:
    vsapi_basic_event.update(
        {
            "requestContext": {
                "resourcePath": "/device/type",
                "httpMethod": "POST",
            },
            "body": json.dumps(
                {
                    "template_id": "test_id",
                    "payload": [
                        {
                            "name": "test_name",
                            "type": "id",
                        }
                    ],
                }
            ),
        }
    )

    return Request(vsapi_basic_event)


@pytest.fixture(name="vsapi_create_device_type_event")
def fixture_create_device_type_event(vsapi_basic_event: Dict[str, Any]) -> Request:
    vsapi_basic_event.update(
        {
            "requestContext": {
                "resourcePath": "/device/type",
                "httpMethod": "POST",
            },
            "body": json.dumps(
                {
                    "type_id": "test_id",
                    "name": "test_type",
                    "topic": "test_topic",
                    "payload": [
                        {
                            "name": "test_name",
                            "type": "id",
                        }
                    ],
                }
            ),
        }
    )

    return Request(vsapi_basic_event)


@pytest.fixture(name="vsapi_update_device_type_event")
def fixture_update_device_type_event(vsapi_basic_event: Dict[str, Any]) -> Request:
    vsapi_basic_event.update(
        {
            "requestContext": {
                "resourcePath": "/device/type",
                "httpMethod": "PUT",
            },
            "body": json.dumps(
                {
                    "type_id": "test_id",
                    "name": "test_type",
                    "topic": "test_topic",
                    "payload": [
                        {
                            "name": "test_name",
                            "type": "id",
                        }
                    ],
                }
            ),
        }
    )

    return Request(vsapi_basic_event)


@pytest.fixture(name="vsapi_create_simulation_event")
def fixture_create_simulation_event(vsapi_basic_event: Dict[str, Any]) -> Request:
    vsapi_basic_event.update(
        {
            "requestContext": {
                "resourcePath": "/simulation",
                "httpMethod": "POST",
            },
            "body": json.dumps(
                {
                    "sim_id": "test_id",
                    "name": "test_name",
                    "stage": "sleeping",
                    "duration": 10,
                    "interval": 1,
                    "devices": [
                        {
                            "type_id": "test_id",
                            "name": "test_name",
                            "amount": "1",
                        }
                    ],
                }
            ),
        }
    )

    return Request(vsapi_basic_event)


@pytest.fixture(name="vsapi_update_simulation_by_id_event")
def fixture_update_simulation_by_id_event(vsapi_basic_event: Dict[str, Any]) -> Request:
    vsapi_basic_event.update(
        {
            "requestContext": {
                "resourcePath": "/simulation",
                "httpMethod": "PUT",
            },
            "body": json.dumps(
                {
                    "sim_id": "test_id",
                    "name": "test_name",
                    "stage": "sleeping",
                    "duration": 10,
                    "interval": 1,
                    "devices": [
                        {
                            "type_id": "test_id",
                            "name": "test_name",
                            "amount": "1",
                        }
                    ],
                    "action": "start",
                }
            ),
        }
    )

    return Request(vsapi_basic_event)


@pytest.fixture(name="vsapi_update_simulations_event")
def fixture_update_simulations_event(vsapi_basic_event: Dict[str, Any]) -> Request:
    vsapi_basic_event.update(
        {
            "requestContext": {
                "resourcePath": "/simulation",
                "httpMethod": "PUT",
            },
            "body": json.dumps(
                {
                    "action": "start",
                    "simulations": [
                        {
                            "sim_id": "test_id",
                            "name": "test_name",
                            "stage": "sleeping",
                            "duration": 10,
                            "interval": 1,
                            "devices": [
                                {
                                    "type_id": "test_id",
                                    "name": "test_name",
                                    "amount": "1",
                                }
                            ],
                        }
                    ],
                }
            ),
        }
    )

    return Request(vsapi_basic_event)
