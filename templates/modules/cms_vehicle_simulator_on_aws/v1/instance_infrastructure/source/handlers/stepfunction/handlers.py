# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json
import os
from typing import Any, Dict

# Third Party Libraries
import boto3
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from boto3.dynamodb.types import TypeDeserializer
from botocore.config import Config

# Connected Mobility Solution on AWS
from .provision import DeviceProvisioner
from .random_sim import GenericSim

tracer = Tracer()
logger = Logger()


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def provision_handler(event: Dict[str, Any], context: LambdaContext) -> None:
    region, account_id = context.invoked_function_arn.split(":", 5)[2:4]
    provisioner = DeviceProvisioner(
        account_id,
        region,
        event["simulation"]["sim_id"],
        user_agent_string=os.environ["USER_AGENT_STRING"],
    )

    device_name = f"{event['info']['name']['S']}-{event['index']}"

    secrets = provisioner.create_device_secrets(device_name)
    provisioner.create_thing(device_name, secrets["keys"]["certificateArn"])


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def data_sim_handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    simulation = event["simulation"]
    options: Dict[str, Any] = event.get("options", {"restart": False})
    options["context"] = context

    try:
        options["counter"] += 1
    except KeyError:
        options["counter"] = 0

    try:
        options["runtime"] += int(simulation["interval"])
    except KeyError:
        options["runtime"] = 0
    except ValueError:
        # something is wrong with interval
        options["runtime"] = int(simulation["duration"])

    # handle device stage
    sim_fields = TypeDeserializer().deserialize(event["info"]["payload"])
    logger.info("sim fields", extra={"simfields": sim_fields})
    data = {}
    for field in sim_fields:
        if field.get("static"):
            data[field["name"]] = (
                field.get("default")
                or event.get("devices", {}).get(field["name"])
                or getattr(GenericSim, f"generic_sim_{field['type']}")(
                    field, counter=options["counter"]
                )
            )
        else:
            data[field["name"]] = getattr(GenericSim, f"generic_sim_{field['type']}")(
                field, counter=options["counter"]
            )

    iot_endpoint = boto3.client(
        "iot-data", config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"])
    )
    iot_endpoint.publish(
        topic=f"{os.environ.get('TOPIC_PREFIX', 'cms/data/simulated')}/{event['info']['name']['S']}-{event['index']}",  # default topic prefix for tests
        payload=json.dumps(data),
        qos=0,
    )

    del options["context"]

    return options


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def cleanup_handler(event: Dict[str, Any], context: LambdaContext) -> None:
    region, account_id = context.invoked_function_arn.split(":", 5)[2:4]
    device_provisioner = DeviceProvisioner(
        account_id,
        region,
        event["simulation"]["sim_id"],
        user_agent_string=os.environ["USER_AGENT_STRING"],
    )

    for secret_arn in device_provisioner.get_simulated_secrets():
        device_provisioner.delete_secretsmanager_secret(secret_arn)

    for thing in device_provisioner.get_simulated_things():
        device_provisioner.delete_iot_thing(thing["thingName"])
