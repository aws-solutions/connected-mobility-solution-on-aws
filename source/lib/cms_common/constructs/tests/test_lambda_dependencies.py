# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from os.path import abspath, dirname

# Third Party Libraries
from syrupy.types import SerializableData

# AWS Libraries
from aws_cdk import assertions


def test_lambda_dependencies_snapshot(
    empty_lambda_dependencies_stack: assertions.Template,
    snapshot_json_with_matcher: SerializableData,
) -> None:

    assert empty_lambda_dependencies_stack.to_json() == snapshot_json_with_matcher


def test_requiremments_file_correctly_populated(
    populated_lambda_dependencies_stack: assertions.Template,
) -> None:
    with open(
        f"{dirname(abspath(__file__))}/mock_dependency_layer/requirements.txt",
        "r",
        encoding="utf-8",
    ) as req_file:
        generated_requirements = set(req_file.read().splitlines())

    expected_requirements = set(
        ["package_a >=2.28.1", "package_b", "package_c[essential] ", "./../lib"]
    )

    assert generated_requirements == expected_requirements
