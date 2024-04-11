# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import List

# AWS Libraries
from aws_cdk import Stack, aws_ec2
from constructs import Construct

# Connected Mobility Solution on AWS
from ..aspects.nag_suppression import NagSuppression, NagType
from ..policy_generators.ec2_vpc import generate_ec2_vpc_policy
from .vpc_construct import VpcConstruct


class CDKLambdasVpcConfigConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        vpc_construct: VpcConstruct,
        subnets: List[str],
    ) -> None:
        super().__init__(scope, construct_id)

        base_security_group = aws_ec2.SecurityGroup(
            self, "security-group", allow_all_outbound=True, vpc=vpc_construct.vpc  # type: ignore[arg-type] # NOSONAR
        )

        self.security_groups = [
            Stack.of(self).get_logical_id(base_security_group.node.default_child)  # type: ignore[arg-type]
        ]

        self.subnets = subnets
        self.ec2_vpc_policy_document = generate_ec2_vpc_policy(
            self,
            vpc_construct=vpc_construct,
            subnet_selection=vpc_construct.private_subnet_selection,
            authorized_service="lambda.amazonaws.com",
        )

        NagSuppression.add_inline_suppression(
            node=base_security_group.node.default_child,
            suppression={
                "rules_to_suppress": [
                    {
                        "id": "W5",
                        "reason": "Unable to know egress requirement. leaving open for now",
                    },
                    {
                        "id": "W40",
                        "reason": "Unable to know egress requirement. leaving open for now",
                    },
                ]
            },
            nag_type=NagType.CFN_NAG,
        )
