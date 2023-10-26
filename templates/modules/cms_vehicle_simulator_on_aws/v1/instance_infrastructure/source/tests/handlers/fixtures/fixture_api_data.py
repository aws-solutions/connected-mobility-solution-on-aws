# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json
from typing import Generator

# Third Party Libraries
import boto3
import pytest
from moto import mock_dynamodb, mock_stepfunctions  # type: ignore

# Connected Mobility Solution on AWS
from ....handlers.api.vs_api.chalicelib.stepfunctions import StepFunctionsStateMachine


@pytest.fixture(name="dynamodb_table")
def fixture_dynamodb_table() -> Generator[str, None, None]:
    with mock_dynamodb():
        table_name = "test_table"
        table = boto3.resource("dynamodb")
        table.create_table(
            AttributeDefinitions=[
                {
                    "AttributeName": "id",
                    "AttributeType": "S",
                },
            ],
            TableName=table_name,
            KeySchema=[
                {"AttributeName": "id", "KeyType": "HASH"},
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        table.Table(table_name).put_item(
            Item={
                "id": "test_id_1",
                "test_val": "test_val_1",
            }
        )
        table.Table(table_name).put_item(
            Item={
                "id": "test_id_2",
                "test_val": "test_val_2",
            }
        )
        yield table_name


@pytest.fixture(name="step_function")
def fixture_step_function() -> Generator[StepFunctionsStateMachine, None, None]:
    with mock_stepfunctions():
        step_function = StepFunctionsStateMachine()
        state_machine_name = "test_state_machine_name"
        response = step_function.stepfunctions_client.create_state_machine(
            name=state_machine_name,
            definition=json.dumps(None),
            roleArn="arn:aws:iam::123456789012:role/test_role",
        )
        step_function.state_machine_name = state_machine_name
        step_function.state_machine_arn = response["stateMachineArn"]
        yield step_function
