# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
# AWS Libraries

# AWS Libraries
from aws_cdk import Stack, aws_ec2, aws_iam
from constructs import Construct

# Connected Mobility Solution on AWS
from ..constructs.vpc_construct import VpcConstruct


def generate_ec2_vpc_policy(
    self: Construct,
    vpc_construct: VpcConstruct,
    subnet_selection: aws_ec2.SubnetSelection,
    authorized_service: str,
) -> aws_iam.PolicyDocument:
    return aws_iam.PolicyDocument(
        statements=[
            aws_iam.PolicyStatement(
                effect=aws_iam.Effect.ALLOW,
                actions=[
                    "ec2:CreateNetworkInterfacePermission",
                ],
                resources=[
                    Stack.of(self).format_arn(
                        partition=Stack.of(self).partition,
                        service="ec2",
                        region=Stack.of(self).region,
                        account=Stack.of(self).account,
                        resource="network-interface",
                        resource_name="*",
                    ),
                ],
                conditions={
                    "StringEquals": {
                        "ec2:Subnet": [
                            Stack.of(self).format_arn(
                                partition=Stack.of(self).partition,
                                service="ec2",
                                region=Stack.of(self).region,
                                account=Stack.of(self).account,
                                resource="subnet",
                                resource_name=subnet_id,
                            )
                            for subnet_id in vpc_construct.vpc.select_subnets(  # type: ignore[union-attr]
                                subnet_selection
                            ).get(
                                "subnetIds"
                            )
                        ],
                        "ec2:AuthorizedService": authorized_service,
                    }
                },
            ),
            aws_iam.PolicyStatement(
                actions=[
                    "ec2:DescribeNetworkInterfaces",
                    "ec2:CreateNetworkInterface",
                    "ec2:DeleteNetworkInterface",
                ],
                effect=aws_iam.Effect.ALLOW,
                resources=["*"],
            ),
        ]
    )
