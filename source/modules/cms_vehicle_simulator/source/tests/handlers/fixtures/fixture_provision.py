# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0


# Standard Library
# mypy: disable-error-code=misc
import json
import os
from typing import Any, Dict, Generator

# Third Party Libraries
import pytest
from moto import mock_aws

# AWS Libraries
import boto3

# Connected Mobility Solution on AWS
from ....handlers.stepfunction.function.provision import DeviceProvisioner


@pytest.fixture(name="device_provisioner")
def fixture_device_provisioner() -> Generator[DeviceProvisioner, None, None]:
    with mock_aws():
        os.environ["SIMULATOR_THING_GROUP_NAME"] = "test-thing-group"
        device_provisioner = DeviceProvisioner(
            "test_account_id",
            "us-east-1",
            "test_simulation_id",
            os.environ["USER_AGENT_STRING"],
        )
        device_provisioner.iot_client().create_thing_group(
            thingGroupName=os.environ.get("SIMULATOR_THING_GROUP_NAME", "")
        )
        yield device_provisioner


@pytest.fixture(name="provision_event")
def fixture_provision_event() -> Dict[str, Any]:
    return {
        "info": {
            "name": {
                "S": "test_device",
            },
        },
        "index": 0,
        "simulation": {"sim_id": "test_simulation_id"},
    }


@pytest.fixture(name="cleanup_event")
def fixture_cleanup_event() -> Dict[str, Any]:
    return {"simulation": {"sim_id": "test_simulation_id"}}


@pytest.fixture(name="provisioned_secrets")
@mock_aws
def fixture_provisioned_secrets() -> Dict[str, Any]:
    device_name = "test-device"
    iot_client = boto3.client("iot")
    secrets_manager_client = boto3.client("secretsmanager")

    keys_and_cert = iot_client.create_keys_and_certificate()
    secret = secrets_manager_client.create_secret(
        Name=f"{device_name}-secret",
        Description=f"Keys and certificate for device {device_name} connecting to iot-core",
        SecretString=json.dumps(keys_and_cert),
        Tags=[{"Key": "cms-simulated-vehicle", "Value": "test_simulation_id"}],
    )

    return {
        "keys": keys_and_cert,
        "secret": secret,
    }


@pytest.fixture(name="provisioned_thing")
@mock_aws
def fixture_provisioned_thing() -> Dict[str, Any]:
    device_name = "test-device"
    iot_client = boto3.client("iot")

    thing = iot_client.create_thing(
        thingName=device_name,
        attributePayload={
            "attributes": {
                "simulation_id": "test_simulation_id",
            }
        },
    )

    return thing  # type: ignore


@pytest.fixture(name="provisioned_policy")
@mock_aws
def fixture_provisioned_policy() -> Dict[str, Any]:
    device_name = "test-device"
    iot_client = boto3.client("iot")

    device_policy = iot_client.create_policy(
        policyName=f"{device_name}-policy",
        policyDocument=json.dumps(
            {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": "iot:Publish",
                        "Resource": "*",
                    },
                ],
            }
        ),
    )

    return {
        "policy_name": device_policy["policyName"],
    }
