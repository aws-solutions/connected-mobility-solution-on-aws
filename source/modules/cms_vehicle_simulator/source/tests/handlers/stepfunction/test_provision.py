# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
# mypy: disable-error-code=misc
import re
from typing import Any, Dict
from unittest.mock import MagicMock

# Third Party Libraries
import pytest

# AWS Libraries
from aws_lambda_powertools.utilities.typing import LambdaContext

# Connected Mobility Solution on AWS
from ....handlers.stepfunction.function.handlers import (
    cleanup_handler,
    provision_handler,
)
from ....handlers.stepfunction.function.provision import DeviceProvisioner


def test_provision_handler(
    provision_event: Dict[str, Any],
    context: LambdaContext,
    device_provisioner: DeviceProvisioner,
) -> None:
    provision_handler(provision_event, context)

    device_name = f"{provision_event['info']['name']['S']}-{provision_event['index']}"
    thing = device_provisioner.iot_client().describe_thing(thingName=device_name)
    assert isinstance(thing["thingArn"], str)

    secret = device_provisioner.secret_manager_client().describe_secret(
        SecretId=f"vs-device/{device_name}-secret"
    )
    assert isinstance(secret, dict)


def test_cleanup_handler(
    cleanup_event: Dict[str, Any],
    context: LambdaContext,
    device_provisioner: DeviceProvisioner,
    mocker: MagicMock,
) -> None:
    mocked_get_simulated_secrets: MagicMock = mocker.patch.object(
        DeviceProvisioner,
        "get_simulated_secrets",
        return_value=[{"test_secret_arn"}],
    )
    mocked_delete_secretsmanager_secret: MagicMock = mocker.patch.object(
        DeviceProvisioner, "delete_secretsmanager_secret"
    )
    mocked_get_simulated_things: MagicMock = mocker.patch.object(
        DeviceProvisioner,
        "get_simulated_things",
        return_value=[{"thingName": "test_thing"}],
    )
    mocked_delete_iot_thing: MagicMock = mocker.patch.object(
        DeviceProvisioner, "delete_iot_thing"
    )

    cleanup_handler(cleanup_event, context)

    mocked_get_simulated_secrets.assert_called_once()
    mocked_delete_secretsmanager_secret.assert_called_once()
    mocked_get_simulated_things.assert_called_once()
    mocked_delete_iot_thing.assert_called_once()


def test_create_device_secrets(device_provisioner: DeviceProvisioner) -> None:
    device_name = "test-device"
    secrets = device_provisioner.create_device_secrets(device_name)

    assert isinstance(secrets["keys"]["certificateArn"], str)
    assert re.match("^[0-9a-f]*$", secrets["keys"]["certificateId"])
    assert isinstance(secrets["keys"]["certificatePem"], str)
    assert isinstance(secrets["keys"]["keyPair"]["PublicKey"], str)
    assert isinstance(secrets["keys"]["keyPair"]["PrivateKey"], str)
    assert isinstance(secrets["secret"]["ARN"], str)
    assert secrets["secret"]["Name"] == f"vs-device/{device_name}-secret"


def test_create_thing(
    device_provisioner: DeviceProvisioner, provisioned_secrets: Dict[str, Any]
) -> None:
    device_name = "test-device"
    thing = device_provisioner.create_thing(
        device_name, provisioned_secrets["keys"]["certificateArn"]
    )

    assert isinstance(thing["thing"]["thingName"], str)
    assert isinstance(thing["thing"]["thingArn"], str)
    assert isinstance(thing["policy"]["policyName"], str)
    assert isinstance(thing["policy"]["policyArn"], str)


def test_get_simulated_things(
    device_provisioner: DeviceProvisioner, provisioned_thing: Dict[str, Any]
) -> None:
    result = list(device_provisioner.get_simulated_things())
    assert len(result) == 1
    assert isinstance(result[0], dict)


def test_get_simulated_secrets(
    device_provisioner: DeviceProvisioner, mocker: MagicMock
) -> None:
    mocked_get_paginator: MagicMock = mocker.patch(
        "botocore.client.BaseClient._make_api_call",
        return_value={"ResourceTagMappingList": [{"ResourceARN": "test_resource_arn"}]},
    )
    result = list(device_provisioner.get_simulated_secrets())
    mocked_get_paginator.assert_called_once()
    assert len(result) == 1
    assert isinstance(result[0], str)


def test_delete_iot_thing(
    device_provisioner: DeviceProvisioner, provisioned_thing: Dict[str, Any]
) -> None:
    device_provisioner.delete_iot_thing(provisioned_thing["thingName"])

    with pytest.raises(
        device_provisioner.iot_client().exceptions.ResourceNotFoundException
    ):
        device_provisioner.iot_client().describe_thing(
            thingName=provisioned_thing["thingName"]
        )


def test_delete_iot_principal(
    device_provisioner: DeviceProvisioner, provisioned_secrets: Dict[str, Any]
) -> None:
    device_provisioner.delete_iot_principal(
        provisioned_secrets["keys"]["certificateId"]
    )

    with pytest.raises(
        device_provisioner.iot_client().exceptions.ResourceNotFoundException
    ):
        device_provisioner.iot_client().describe_certificate(
            certificateId=provisioned_secrets["keys"]["certificateId"]
        )


def test_delete_iot_policy(
    device_provisioner: DeviceProvisioner, provisioned_policy: Dict[str, Any]
) -> None:
    device_provisioner.delete_iot_policy(provisioned_policy["policy_name"])

    with pytest.raises(
        device_provisioner.iot_client().exceptions.ResourceNotFoundException
    ):
        device_provisioner.iot_client().get_policy(
            policyName=provisioned_policy["policy_name"]
        )


def test_delete_secretsmanager_secret(
    device_provisioner: DeviceProvisioner, provisioned_secrets: Dict[str, Any]
) -> None:
    secret_arn = provisioned_secrets["secret"]["ARN"]
    device_provisioner.delete_secretsmanager_secret(secret_arn)

    with pytest.raises(
        device_provisioner.secret_manager_client().exceptions.ResourceNotFoundException
    ):
        device_provisioner.secret_manager_client().describe_secret(SecretId=secret_arn)
