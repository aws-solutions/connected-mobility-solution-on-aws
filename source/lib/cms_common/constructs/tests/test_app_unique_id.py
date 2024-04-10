# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
# Standard Library
import re
from typing import Any, Dict

# Third Party Libraries
import pytest
from syrupy.types import SerializableData

# AWS Libraries
from aws_cdk import assertions


def test_app_unique_id_snapshot(
    app_unique_id_stack: assertions.Template,
    snapshot_json_with_matcher: SerializableData,
) -> None:
    assert app_unique_id_stack.to_json() == snapshot_json_with_matcher


@pytest.mark.parametrize(
    "cfn_parameter_value, is_valid",
    [
        ("abc", True),
        ("abcdefghij", True),
        ("ab1", True),
        ("ab-1", True),
        ("1a-2b-3c", True),
        ("ab", False),  # too short
        ("abcdefghijk", False),  # too long
        ("abC", False),  # uppercase not allowed
        ("ab#", False),  # special character not allowed
        ("ab_cd", False),  # underscore not allowed
    ],
)
def test_app_unique_id_allowed_values(
    app_unique_id_cfn_parameter: Dict[str, Any],
    cfn_parameter_value: str,
    is_valid: bool,
) -> None:
    def validate(value: str) -> bool:
        if (
            len(value) < app_unique_id_cfn_parameter["MinLength"]
            or len(value) > app_unique_id_cfn_parameter["MaxLength"]
        ):
            return False
        match = re.match(app_unique_id_cfn_parameter["AllowedPattern"], value)
        return match is not None

    assert validate(cfn_parameter_value) == is_valid
