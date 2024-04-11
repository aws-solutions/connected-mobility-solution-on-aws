# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import functools
import os
from functools import partial
from typing import Any, Dict, List
from uuid import uuid4

# Third Party Libraries
import arrow
from cattrs import ClassValidationError, structure, unstructure

# AWS Libraries
from aws_lambda_powertools import Logger, Tracer
from chalice import Chalice, CORSConfig, Response  # type: ignore[attr-defined]
from chalice.app import BadRequestError, CognitoUserPoolAuthorizer, Request

# CMS Common Library
from cms_common.boto3_wrappers.dynamo_crud import DynHelpers

try:
    # Connected Mobility Solution on AWS
    from .chalicelib.dynamo_schema import (
        DeviceType,
        DeviceTypeTemplate,
        Simulation,
        UpdateSimulationsRequest,
    )
    from .chalicelib.iot_core_cleanup import IotCoreCleanup
    from .chalicelib.stepfunctions import StepFunctionsStateMachine
except ImportError:
    # Third Party Libraries
    from chalicelib.dynamo_schema import DeviceType  # type: ignore
    from chalicelib.dynamo_schema import DeviceTypeTemplate  # type: ignore
    from chalicelib.dynamo_schema import Simulation  # type: ignore
    from chalicelib.dynamo_schema import UpdateSimulationsRequest  # type: ignore
    from chalicelib.iot_core_cleanup import IotCoreCleanup  # type: ignore
    from chalicelib.stepfunctions import StepFunctionsStateMachine  # type: ignore

tracer = Tracer()
logger = Logger()
app = Chalice(app_name="VSApi")

# This may apply it to every endpoint
app.api.cors = CORSConfig(
    allow_origin=os.environ.get("CROSS_ORIGIN_DOMAIN", ""),
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Amz-Date",
        "X-Amz-Security-Token",
        "X-Api-Key",
    ],
)

authorizer = CognitoUserPoolAuthorizer(
    "vehicle-simulator-api-authorizer",
    provider_arns=[os.environ.get("USER_POOL_ARN")],  # type: ignore[list-item]
    header="Authorization",
)

success_response = partial(
    Response,
    status_code=200,
    headers={
        "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload"
    },
)


def get_current_request() -> Request:
    assert isinstance(app.current_request, Request)  # nosec
    return app.current_request


@app.route("/template/{template_id}", methods=["GET"], authorizer=authorizer)
@tracer.capture_method
def get_template_by_template_id(template_id: str) -> Response:
    return success_response(
        body=DynHelpers.get_item(
            os.environ["DYN_TEMPLATES_TABLE"],
            {"template_id": template_id},
        )
    )


@app.route("/template", methods=["GET"], authorizer=authorizer)
@tracer.capture_method
def get_all_template_names() -> Response:
    return success_response(
        body=next(
            DynHelpers.dyn_scan(
                os.environ["DYN_TEMPLATES_TABLE"],
                Select="SPECIFIC_ATTRIBUTES",
                ProjectionExpression="type, version",
            )
        )
    )


@app.route("/template", methods=["POST"], authorizer=authorizer)
@tracer.capture_method
def create_new_template() -> Response:
    try:
        json_body = get_current_request().json_body
        template = structure(json_body, DeviceTypeTemplate)
        DynHelpers.put_item(os.environ["DYN_TEMPLATES_TABLE"], unstructure(template))
    except ClassValidationError as exc:
        logger.error(
            "Error validating request body",
            extras={"request_body": json_body},
            exc_info=True,
        )
        raise BadRequestError("Invalid request body") from exc

    return success_response(body={})


@app.route("/template", methods=["PUT"], authorizer=authorizer)
@tracer.capture_method
def update_template() -> Response:
    try:
        json_body = get_current_request().json_body
        template = structure(json_body, DeviceTypeTemplate)
        DynHelpers.update_item(os.environ["DYN_TEMPLATES_TABLE"], unstructure(template))
    except ClassValidationError as exc:
        logger.error(
            "Error validating request body",
            extras={"request_body": json_body},
            exc_info=True,
        )
        raise BadRequestError("Invalid request body") from exc

    return success_response(body={})


@app.route("/template/{template_id}", methods=["DELETE"], authorizer=authorizer)
@tracer.capture_method
def delete_template(template_id: str) -> Response:
    DynHelpers.delete_item(
        os.environ["DYN_TEMPLATES_TABLE"], {"template_id": template_id}
    )

    return success_response(body={})


@app.route("/device", methods=["GET"], authorizer=authorizer)
@tracer.capture_method
def get_devices() -> Response:
    return success_response(
        body=next(DynHelpers.dyn_scan(table=os.environ["DYN_DEVICE_TYPES_TABLE"]))
    )


@app.route("/device/type", methods=["GET"], authorizer=authorizer)
@tracer.capture_method
def get_device_types() -> Response:
    return success_response(
        body=next(DynHelpers.dyn_scan(table=os.environ["DYN_DEVICE_TYPES_TABLE"]))
    )


@app.route("/device/type", methods=["POST"], authorizer=authorizer)
@tracer.capture_method
def create_device_type() -> Response:
    try:
        json_body = get_current_request().json_body
        if not json_body["type_id"]:
            json_body["type_id"] = str(uuid4())
        device = structure(json_body, DeviceType)
        DynHelpers.put_item(os.environ["DYN_DEVICE_TYPES_TABLE"], unstructure(device))
    except ClassValidationError as exc:
        logger.error(
            "Error validating request body",
            extras={"request_body": json_body},
            exc_info=True,
        )
        raise BadRequestError("Invalid request body") from exc

    return success_response(body={})


@app.route("/device/type/{device_type_id}", methods=["GET"], authorizer=authorizer)
@tracer.capture_method
def get_device_type_by_id(device_type_id: str) -> Response:
    return success_response(
        body=DynHelpers.get_item(
            os.environ["DYN_DEVICE_TYPES_TABLE"], {"id": device_type_id}
        )
    )


@app.route("/device/type", methods=["PUT"], authorizer=authorizer)
@tracer.capture_method
def update_device_type_by_id() -> Response:
    try:
        json_body = get_current_request().json_body
        device = structure(json_body, DeviceType)
        DynHelpers.update_item(
            os.environ["DYN_DEVICE_TYPES_TABLE"], unstructure(device)
        )
    except ClassValidationError as exc:
        logger.error(
            "Error validating request body",
            extras={"request_body": json_body},
            exc_info=True,
        )
        raise BadRequestError("Invalid request body") from exc

    return success_response(body={})


@app.route("/device/type/{device_type_id}", methods=["DELETE"], authorizer=authorizer)
@tracer.capture_method
def delete_device_type_by_id(device_type_id: str) -> Response:
    return success_response(
        body=DynHelpers.delete_item(
            os.environ["DYN_DEVICE_TYPES_TABLE"], {"type_id": device_type_id}
        )
    )


@app.route("/simulation", methods=["GET"], authorizer=authorizer)
@tracer.capture_method
def get_simulations() -> Response:
    request_object = get_current_request()
    if request_object:
        request = request_object.to_dict()
        if (
            request["query_params"]
            and request["query_params"].get("op") == "getRunningStat"
        ):
            stat_data = DynHelpers.get_all(
                table=os.environ["DYN_SIMULATIONS_TABLE"],
                FilterExpression="stage = :stage",
                ExpressionAttributeValues={":stage": "running"},
                ProjectionExpression="devices",
            )
            logger.info("stat data", extra={"stat_data": stat_data})

            def device_reduce(total: int, current: Dict[str, List[Any]]) -> int:
                if isinstance(total, dict):
                    return len(total["devices"]) + len(current["devices"])
                return total + len(current["devices"])

            if not stat_data:
                return_stats = {"devices": 0, "sims": 0}
            else:
                return_stats = {
                    "devices": functools.reduce(device_reduce, stat_data, 0),
                    "sims": len(stat_data),
                }

            return success_response(body=return_stats)

    return success_response(
        body=next(DynHelpers.dyn_scan(table=os.environ["DYN_SIMULATIONS_TABLE"]))
    )


@app.route("/simulation", methods=["POST"], authorizer=authorizer)
@tracer.capture_method
def create_simulation() -> Response:
    try:
        json_body = get_current_request().json_body
        json_body.update({"stage": "sleeping", "runs": 0, "last_run": None})
        if not json_body["sim_id"]:
            json_body["sim_id"] = str(uuid4())
        simulation = structure(json_body, Simulation)
        DynHelpers.put_item(
            os.environ["DYN_SIMULATIONS_TABLE"], unstructure(simulation)
        )
    except ClassValidationError as exc:
        logger.error(
            "Error validating request body",
            extras={"request_body": json_body},
            exc_info=True,
        )
        raise BadRequestError("Invalid request body") from exc

    return success_response(body={})


@app.route("/simulation", methods=["PUT"], authorizer=authorizer)
@tracer.capture_method
def update_simulations() -> Response:
    try:
        json_body = get_current_request().json_body
        update_simulations_request = structure(json_body, UpdateSimulationsRequest)
        for sim in update_simulations_request.simulations:
            logger.info("Updating Simulation: %s", sim.name, extra={"simulation": sim})
            simulation = structure(
                DynHelpers.get_item(
                    os.environ["DYN_SIMULATIONS_TABLE"], {"sim_id": sim.sim_id}
                ),
                Simulation,
            )

            DynHelpers.put_item(
                os.environ["DYN_SIMULATIONS_TABLE"],
                unstructure(
                    act_on_simulation(simulation, update_simulations_request.action)
                ),
            )
    except ClassValidationError as exc:
        logger.error(
            "Error validating request body",
            extras={"request_body": json_body},
            exc_info=True,
        )
        raise BadRequestError("Invalid request body") from exc

    return success_response(body={})


@app.route("/simulation/{simulation_id}", methods=["GET"], authorizer=authorizer)
@tracer.capture_method
def get_simulation_by_id(simulation_id: str) -> Response:
    simulation = DynHelpers.get_item(
        os.environ["DYN_SIMULATIONS_TABLE"], {"sim_id": simulation_id}
    )

    for device in simulation["devices"]:
        device.update(
            DynHelpers.get_item(
                os.environ["DYN_DEVICE_TYPES_TABLE"], {"type_id": device["type_id"]}
            )
        )

    return success_response(body=simulation)


@tracer.capture_method
def act_on_simulation(simulation: Simulation, action: str) -> Simulation:
    simulation_dict: Dict[str, Any] = unstructure(simulation)
    updated_simulation: Simulation

    # start
    if action == "start":
        simulation_dict.update(
            {
                "stage": "running",
                "last_run": arrow.utcnow().isoformat(),
                "runs": simulation.runs + 1,  # type: ignore
            }
        )

        sf_input = {"simulation": simulation_dict}

        state_machine = StepFunctionsStateMachine()
        state_machine.find(os.environ["SIMULATOR_STATE_MACHINE_NAME"])
        logger.info("Starting simulation", extra={"input": sf_input})

        simulation_dict["current_run_arn"] = state_machine.start_run(
            f"{simulation.name[:40]}-{str(uuid4())}", sf_input
        )

        updated_simulation = structure(simulation_dict, Simulation)

    # stop
    if action == "stop":
        simulation_dict["stage"] = "sleeping"
        updated_simulation = structure(simulation_dict, Simulation)

        state_machine = StepFunctionsStateMachine()
        state_machine.find(os.environ["SIMULATOR_STATE_MACHINE_NAME"])
        logger.info(
            "Stopping simulation", extra={"simulation": unstructure(simulation)}
        )
        state_machine.stop_run(
            simulation.current_run_arn, "User request to stop simulation"  # type: ignore
        )
        logger.info(
            "Cleaning up provisioned resources for simulation: %s", simulation.sim_id
        )
        IotCoreCleanup().cleanup(simulation.sim_id)

    return updated_simulation


@app.route("/simulation/{simulation_id}", methods=["PUT"], authorizer=authorizer)
@tracer.capture_method
def update_simulation_by_id(simulation_id: str) -> Response:
    try:
        json_body = get_current_request().json_body
        logger.info("Updating %s", simulation_id, extra={"simulation": json_body})
        simulation = structure(
            DynHelpers.get_item(
                os.environ["DYN_SIMULATIONS_TABLE"], {"sim_id": simulation_id}
            ),
            Simulation,
        )

        DynHelpers.put_item(
            os.environ["DYN_SIMULATIONS_TABLE"],
            unstructure(act_on_simulation(simulation, json_body["action"])),
        )
    except ClassValidationError as exc:
        logger.error(
            "Error validating request body",
            extras={"request_body": json_body},
            exc_info=True,
        )
        raise BadRequestError("Invalid request body") from exc

    return success_response(body={})


@app.route("/simulation/{simulation_id}", methods=["DELETE"], authorizer=authorizer)
@tracer.capture_method
def delete_simulation_by_id(simulation_id: str) -> Response:
    return success_response(
        body=DynHelpers.delete_item(
            os.environ["DYN_SIMULATIONS_TABLE"], {"sim_id": simulation_id}
        )
    )
