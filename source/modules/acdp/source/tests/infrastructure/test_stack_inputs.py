# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import re
from typing import Any, Dict, List

# Third Party Libraries
import pytest


@pytest.mark.parametrize(
    "cfn_parameter_names, cfn_parameter_value, is_valid",
    [
        (["UserEmail"], "jie_liu@example.com", True),
        (["UserEmail"], "jie.liu@example.com", True),
        (["UserEmail"], "abc.123@example.com", True),
        (["UserEmail"], "jie_liu@example", False),
        (["UserEmail"], "_jie_liu@example", False),
        (["UserEmail"], "jie_liu@", False),
        (["UserEmail"], "jie_liu", False),
        (["UserEmail"], "a", False),
        (["Route53ZoneName", "Route53BaseDomain"], "example.com", True),
        (["Route53ZoneName", "Route53BaseDomain"], "a.example.jp", True),
        (["Route53ZoneName", "Route53BaseDomain"], "123.example123.co.in", True),
        (["Route53ZoneName", "Route53BaseDomain"], "exam-ple.com", True),
        (["Route53ZoneName", "Route53BaseDomain"], "example.c", True),
        (["Route53ZoneName", "Route53BaseDomain"], "example.", False),
        (["Route53ZoneName", "Route53BaseDomain"], "-example.com", False),
        (["Route53ZoneName", "Route53BaseDomain"], "123@example", False),
        (["Route53ZoneName", "Route53BaseDomain"], "example", False),
        (["Route53ZoneName", "Route53BaseDomain"], "ex$mple.com", False),
        (["BackstageName", "BackstageOrg"], "backstage name", True),
        (["BackstageName", "BackstageOrg"], "123 org", True),
        (["BackstageName", "BackstageOrg"], "name @123", False),
        (["BackstageName", "BackstageOrg"], "backstage.name", False),
        (["BackstageName", "BackstageOrg"], " backstage", False),
        (["BackstageName", "BackstageOrg"], " ", False),
    ],
)
def test_cfn_parameter_validators(
    acdp_stack_parameters: Dict[str, Any],
    cfn_parameter_names: List[str],
    cfn_parameter_value: str,
    is_valid: bool,
) -> None:
    for cfn_parameter_name in cfn_parameter_names:
        pattern = acdp_stack_parameters[cfn_parameter_name]["AllowedPattern"]
        match = re.match(pattern, cfn_parameter_value)
        assert (match is not None) == is_valid
