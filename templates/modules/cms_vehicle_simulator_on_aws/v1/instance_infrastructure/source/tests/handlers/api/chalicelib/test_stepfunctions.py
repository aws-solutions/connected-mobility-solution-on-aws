# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0


# Standard Library
# mypy: disable-error-code=misc
import json

# Third Party Libraries
import pytest
from moto import mock_aws  # type: ignore

# Connected Mobility Solution on AWS
from .....handlers.api.vs_api.chalicelib.stepfunctions import StepFunctionsStateMachine


@mock_aws
def test__init__() -> None:
    step_function = StepFunctionsStateMachine()
    assert step_function.stepfunctions_client


@mock_aws
def test_create() -> None:
    step_function = StepFunctionsStateMachine()
    step_function_name = "test_state_machine_name"
    step_function_role_arn = "arn:aws:iam::123456789012:role/test_role"
    state_machine_arn = step_function.create(
        step_function_name,
        {"test": "test"},
        step_function_role_arn,
    )

    assert step_function.state_machine_name == step_function_name

    description = step_function.stepfunctions_client.describe_state_machine(
        stateMachineArn=state_machine_arn  # type: ignore
    )
    assert description["stateMachineArn"] == state_machine_arn
    assert description["roleArn"] == step_function_role_arn
    assert description["name"] == step_function_name
    assert description["status"] == "ACTIVE"


def test_update(step_function: StepFunctionsStateMachine) -> None:
    new_role_arn = "arn:aws:iam::123456789012:role/test_role_updated"
    new_definition = {"test_key": "test_val"}
    step_function.update(new_definition, new_role_arn)
    description = step_function.stepfunctions_client.describe_state_machine(
        stateMachineArn=step_function.state_machine_arn  # type: ignore
    )

    assert json.loads(description["definition"]) == new_definition
    assert description["roleArn"] == new_role_arn


def test_delete(step_function: StepFunctionsStateMachine) -> None:
    client = step_function.stepfunctions_client
    state_machine_arn = step_function.state_machine_arn
    step_function.delete()
    with pytest.raises(client.exceptions.StateMachineDoesNotExist):
        client.describe_state_machine(stateMachineArn=state_machine_arn)  # type: ignore


def test_find(step_function: StepFunctionsStateMachine) -> None:
    name = step_function.state_machine_name or "test_state_machine"
    arn = str(step_function.find(name))
    assert name in arn


def test_describe(step_function: StepFunctionsStateMachine) -> None:
    description = step_function.describe()
    assert description["stateMachineArn"] == step_function.state_machine_arn
    assert description["name"] == step_function.state_machine_name


def test_start_run(step_function: StepFunctionsStateMachine) -> None:
    run_name = "test_run"
    execution_arn = step_function.start_run(run_name)
    description = step_function.stepfunctions_client.describe_execution(
        executionArn=execution_arn
    )
    assert description["status"] == "RUNNING"


def test_list_runs(step_function: StepFunctionsStateMachine) -> None:
    step_function.stepfunctions_client.start_execution(
        stateMachineArn=step_function.state_machine_arn, name="test_run_1"  # type: ignore
    )
    step_function.stepfunctions_client.start_execution(
        stateMachineArn=step_function.state_machine_arn, name="test_run_2"  # type: ignore
    )
    assert len(step_function.list_runs()) == 2


def test_stop_run(step_function: StepFunctionsStateMachine) -> None:
    response = step_function.stepfunctions_client.start_execution(
        stateMachineArn=step_function.state_machine_arn, name="test_run_1"  # type: ignore
    )
    execution_arn = response["executionArn"]
    step_function.stop_run(execution_arn, "stop_run test")
    description = step_function.stepfunctions_client.describe_execution(
        executionArn=execution_arn
    )
    assert description["status"] == "ABORTED"
