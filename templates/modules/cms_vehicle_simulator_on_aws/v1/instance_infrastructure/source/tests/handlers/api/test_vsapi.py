# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0


# Standard Library
# mypy: disable-error-code=misc
import json
from unittest import mock

# Third Party Libraries
import boto3
from chalice.app import Request
from moto import mock_stepfunctions  # type: ignore[import-untyped]

# Connected Mobility Solution on AWS
from ....handlers.api.vs_api import app
from ....handlers.api.vs_api.chalicelib.dynamo_crud import DynHelpers


### Template Tests ###
def test_create_template(
    vsapi_create_template_event: Request, mocker: mock.MagicMock
) -> None:
    mocked_app_req: mock.MagicMock = mocker.patch.object(
        app,
        "get_current_request",
        return_value=vsapi_create_template_event,
    )
    mocked_put_item: mock.MagicMock = mocker.patch.object(
        DynHelpers,
        "put_item",
        return_value=None,
    )
    response = app.create_new_template()
    assert response.body == {}
    mocked_put_item.assert_called_once()
    mocked_app_req.assert_called_once()


def test_get_template_by_template_id(mocker: mock.MagicMock) -> None:
    mocked_response = {"template_id": "test"}
    mocked_dyn_scan: mock.MagicMock = mocker.patch.object(
        DynHelpers,
        "get_item",
        return_value=(mocked_response),
    )
    response = app.get_template_by_template_id("test")
    assert response.body == mocked_response
    mocked_dyn_scan.assert_called_once()


def test_get_all_template_names(mocker: mock.MagicMock) -> None:
    mocked_response = "template1"
    mocked_dyn_scan: mock.MagicMock = mocker.patch.object(
        DynHelpers,
        "dyn_scan",
        return_value=iter([mocked_response]),
    )
    response = app.get_all_template_names()
    assert response.body == mocked_response
    mocked_dyn_scan.assert_called_once()


def test_update_template(
    vsapi_create_template_event: Request, mocker: mock.MagicMock
) -> None:
    mocked_app_req: mock.MagicMock = mocker.patch.object(
        app,
        "get_current_request",
        return_value=vsapi_create_template_event,
    )
    mocked_put_item: mock.MagicMock = mocker.patch.object(
        DynHelpers,
        "update_item",
        return_value=None,
    )
    response = app.update_template()
    assert response.body == {}
    mocked_app_req.assert_called_once()
    mocked_put_item.assert_called_once()


def test_delete_template(mocker: mock.MagicMock) -> None:
    mocked_put_item: mock.MagicMock = mocker.patch.object(
        DynHelpers,
        "delete_item",
        return_value=None,
    )
    response = app.delete_template("test")
    assert response.body == {}
    mocked_put_item.assert_called_once()


### Device Tests ###
def test_create_device_type(
    vsapi_create_device_type_event: Request, mocker: mock.MagicMock
) -> None:
    mocked_app_req: mock.MagicMock = mocker.patch.object(
        app,
        "get_current_request",
        return_value=vsapi_create_device_type_event,
    )
    mocked_put_item: mock.MagicMock = mocker.patch.object(
        DynHelpers,
        "put_item",
        return_value=None,
    )
    response = app.create_device_type()
    assert response.body == {}
    mocked_put_item.assert_called_once()
    mocked_app_req.assert_called_once()


def test_get_device_type_by_id(mocker: mock.MagicMock) -> None:
    mocked_response = "test"
    mocked_dyn_scan: mock.MagicMock = mocker.patch.object(
        DynHelpers,
        "get_item",
        return_value=mocked_response,
    )
    response = app.get_device_type_by_id("test")
    assert response.body == mocked_response
    mocked_dyn_scan.assert_called_once()


def test_get_device_types(mocker: mock.MagicMock) -> None:
    mocked_response = "test"
    mocked_dyn_scan: mock.MagicMock = mocker.patch.object(
        DynHelpers,
        "dyn_scan",
        return_value=iter([mocked_response]),
    )
    response = app.get_device_types()
    assert response.body == mocked_response
    mocked_dyn_scan.assert_called_once()


def test_get_devices(mocker: mock.MagicMock) -> None:
    mocked_response = "test"
    mocked_dyn_scan: mock.MagicMock = mocker.patch.object(
        DynHelpers,
        "dyn_scan",
        return_value=iter([mocked_response]),
    )
    response = app.get_devices()
    assert response.body == mocked_response
    mocked_dyn_scan.assert_called_once()


def test_update_device_type_by_id(
    vsapi_update_device_type_event: Request, mocker: mock.MagicMock
) -> None:
    mocked_app_req: mock.MagicMock = mocker.patch.object(
        app,
        "get_current_request",
        return_value=vsapi_update_device_type_event,
    )
    mocked_put_item: mock.MagicMock = mocker.patch.object(
        DynHelpers,
        "update_item",
        return_value=None,
    )
    response = app.update_device_type_by_id()
    assert response.body == {}
    mocked_app_req.assert_called_once()
    mocked_put_item.assert_called_once()


def test_delete_device_type_by_id(mocker: mock.MagicMock) -> None:
    mocked_put_item: mock.MagicMock = mocker.patch.object(
        DynHelpers,
        "delete_item",
        return_value=None,
    )
    response = app.delete_device_type_by_id("test")
    assert response.body is None
    mocked_put_item.assert_called_once()


### Simulation Tests ###
def test_create_simulation(
    vsapi_create_simulation_event: Request, mocker: mock.MagicMock
) -> None:
    mocked_app_req: mock.MagicMock = mocker.patch.object(
        app,
        "get_current_request",
        return_value=vsapi_create_simulation_event,
    )
    mocked_put_item: mock.MagicMock = mocker.patch.object(
        DynHelpers,
        "put_item",
        return_value=None,
    )
    response = app.create_simulation()
    assert response.body == {}
    mocked_put_item.assert_called_once()
    mocked_app_req.assert_called_once()


def test_get_simulation_by_id(mocker: mock.MagicMock) -> None:
    mocked_response = {"devices": [{"type_id": "test", "test": "test"}]}
    mocked_dyn_scan: mock.MagicMock = mocker.patch.object(
        DynHelpers,
        "get_item",
        return_value=mocked_response,
    )
    response = app.get_simulation_by_id("test")
    assert response.body == mocked_response
    mocked_dyn_scan.assert_called()


def test_get_simulations(mocker: mock.MagicMock) -> None:
    mocked_response = "test"
    mocked_req = Request(
        event_dict={
            "multiValueQueryStringParameters": {},
            "headers": {},
            "pathParameters": None,
            "isBase64Encoded": False,
            "body": None,
            "requestContext": {
                "resourcePath": "",
                "httpMethod": "GET",
            },
            "stageVariables": None,
        }
    )
    mocked_app_req: mock.MagicMock = mocker.patch.object(
        app, "get_current_request", return_value=mocked_req
    )
    mocked_dyn_scan: mock.MagicMock = mocker.patch.object(
        DynHelpers,
        "dyn_scan",
        return_value=iter([mocked_response]),
    )
    response = app.get_simulations()
    assert response.body == mocked_response
    mocked_dyn_scan.assert_called_once()
    mocked_app_req.assert_called_once()


def test_get_simulations_stats(mocker: mock.MagicMock) -> None:
    mocked_req = Request(
        event_dict={
            "multiValueQueryStringParameters": {
                "op": ["getRunningStat"],
            },
            "headers": {},
            "pathParameters": None,
            "isBase64Encoded": False,
            "body": None,
            "requestContext": {
                "resourcePath": "",
                "httpMethod": "GET",
            },
            "stageVariables": None,
        }
    )
    mocked_app_req: mock.MagicMock = mocker.patch.object(
        app, "get_current_request", return_value=mocked_req
    )
    mocked_dyn_scan: mock.MagicMock = mocker.patch.object(
        DynHelpers,
        "get_all",
        return_value=None,
    )
    response = app.get_simulations()
    assert response.body == {"devices": 0, "sims": 0}
    mocked_dyn_scan.assert_called_once()
    mocked_app_req.assert_called_once()


@mock_stepfunctions
def test_update_simulation(
    vsapi_update_simulations_event: Request, mocker: mock.MagicMock
) -> None:
    stepfunctions_client = boto3.client("stepfunctions")
    stepfunctions_client.create_state_machine(
        name="test",
        definition=json.dumps({"test": "test"}),
        roleArn="arn:aws:iam::123456789012:role/test_role",
    )
    mocked_app_req: mock.MagicMock = mocker.patch.object(
        app,
        "get_current_request",
        return_value=vsapi_update_simulations_event,
    )
    mocked_get_req: mock.MagicMock = mocker.patch.object(
        DynHelpers,
        "get_item",
        return_value={
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
            "runs": 0,
            "current_run_arn": "test_arn",
        },
    )
    mocked_update_req: mock.MagicMock = mocker.patch.object(
        DynHelpers,
        "put_item",
        return_value=None,
    )
    response = app.update_simulations()
    assert response.body == {}
    mocked_app_req.assert_called_once()
    mocked_get_req.assert_called()
    mocked_update_req.assert_called()


@mock_stepfunctions
def test_update_simulation_by_id(
    vsapi_update_simulation_by_id_event: Request, mocker: mock.MagicMock
) -> None:
    stepfunctions_client = boto3.client("stepfunctions")
    stepfunctions_client.create_state_machine(
        name="test",
        definition=json.dumps({"test": "test"}),
        roleArn="arn:aws:iam::123456789012:role/test_role",
    )
    mocked_app_req: mock.MagicMock = mocker.patch.object(
        app,
        "get_current_request",
        return_value=vsapi_update_simulation_by_id_event,
    )
    mocked_get_req: mock.MagicMock = mocker.patch.object(
        DynHelpers,
        "get_item",
        return_value={
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
            "runs": 0,
            "current_run_arn": "test_arn",
        },
    )
    mocked_update_req: mock.MagicMock = mocker.patch.object(
        DynHelpers,
        "put_item",
        return_value=None,
    )

    response = app.update_simulation_by_id("test")
    assert response.body == {}
    mocked_app_req.assert_called_once()
    mocked_get_req.assert_called_once()
    mocked_update_req.assert_called_once()


def test_delete_simulation_by_id(mocker: mock.MagicMock) -> None:
    mocked_get_req: mock.MagicMock = mocker.patch.object(
        DynHelpers,
        "delete_item",
        return_value=None,
    )
    response = app.delete_simulation_by_id("test")
    assert response.body is None
    mocked_get_req.assert_called_once()
