# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Dict, List

# Third Party Libraries
from syrupy.types import SerializableData

# AWS Libraries
from aws_cdk import assertions

# Connected Mobility Solution on AWS
from ..vpc_construct import VpcConstruct


def test_vpc_construct(
    vpc_construct_stack_template: assertions.Template,
    snapshot_json_with_matcher: SerializableData,
) -> None:
    assert vpc_construct_stack_template.to_json() == snapshot_json_with_matcher


def test_vpc_select_subnets(
    vpc_construct: VpcConstruct, subnet_selections: Dict[str, List[str]]
) -> None:
    private_subnet_selection = vpc_construct.vpc.select_subnets(
        selection=vpc_construct.private_subnet_selection
    )
    assert private_subnet_selection["subnetIds"] == subnet_selections["private_subnets"]

    public_subnet_selection = vpc_construct.vpc.select_subnets(
        selection=vpc_construct.public_subnet_selection
    )
    assert public_subnet_selection["subnetIds"] == subnet_selections["public_subnets"]

    isolated_subnet_selection = vpc_construct.vpc.select_subnets(
        selection=vpc_construct.isolated_subnet_selection
    )
    assert (
        isolated_subnet_selection["subnetIds"] == subnet_selections["isolated_subnets"]
    )
