# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library

# AWS Libraries
from aws_cdk import aws_route53
from constructs import Construct


class Route53Construct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        route53_hosted_zone_name: str,
        route53_base_domain: str,
    ) -> None:
        super().__init__(scope, construct_id)

        self.zone_name = route53_hosted_zone_name
        self.base_domain = route53_base_domain

        self.hosted_zone = aws_route53.HostedZone.from_lookup(  # NOTE: MAKE SURE TO EXPORT PROPER AWS_ACCOUNT_ID
            self,
            "hosted-zone",
            domain_name=route53_hosted_zone_name,
        )
