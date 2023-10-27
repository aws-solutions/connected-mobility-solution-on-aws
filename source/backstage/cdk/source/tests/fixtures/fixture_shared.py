# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any, Dict, Generator
from unittest.mock import patch

# Third Party Libraries
import aws_cdk
import pytest

# Connected Mobility Solution on AWS
from ...infrastructure.stacks.stack import BackstageStack


@pytest.fixture(name="mock_ssm_params", scope="session")
def fixture_mock_ssm_params() -> Generator[None, None, None]:
    with patch(
        "aws_cdk.aws_ssm.StringParameter.value_from_lookup",
        new=lambda scope, parameter_name: "TEST",
    ):
        yield


@pytest.fixture(name="template", scope="session")
def fixture_template(mock_ssm_params: Dict[str, Any]) -> aws_cdk.assertions.Template:
    app = aws_cdk.App(
        context={
            "backstage-image-tag": "DUMMY",
        }
    )
    stack = BackstageStack(
        app,
        "test-stack",
        env=aws_cdk.Environment(
            account="test-account-id",
            region="us-west-2",
        ),
    )
    template = aws_cdk.assertions.Template.from_stack(stack)
    return template
