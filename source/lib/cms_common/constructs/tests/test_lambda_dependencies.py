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
        f"{dirname(abspath(__file__))}/mock_dependency_layer/populated/requirements.txt",
        "r",
        encoding="utf-8",
    ) as req_file:
        generated_requirements = set(req_file.read().splitlines())

    expected_requirements = set(
        [
            "-i https://pypi.org/simple",
            "attrs==24.2.0",
            "aws-lambda-powertools[tracer,validation]==3.2.0",
            "aws-xray-sdk==2.14.0",
            "botocore==1.35.53",
            "cattrs==24.1.2",
            "certifi==2024.8.30",
            "cffi==1.17.1",
            "charset-normalizer==3.4.0",
            "./../../../../../../lib",
            "cryptography==43.0.3",
            "fastjsonschema==2.20.0",
            "idna==3.10",
            "jmespath==1.0.1",
            "pycparser==2.22",
            "pyjwt[crypto]==2.9.0",
            "python-dateutil==2.9.0.post0",
            "requests==2.32.3",
            "six==1.16.0",
            "toml==0.10.2",
            "typing-extensions==4.12.2",
            "urllib3==2.2.3",
            "wrapt==1.16.0",
        ]
    )

    assert generated_requirements == expected_requirements
