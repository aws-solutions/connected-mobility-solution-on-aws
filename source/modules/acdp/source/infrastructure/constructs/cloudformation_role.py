# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# AWS Libraries
from aws_cdk import aws_iam
from constructs import Construct


class CloudFormationRoleConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
    ) -> None:
        super().__init__(scope, construct_id)

        self.role = aws_iam.Role(
            self,
            "role",
            assumed_by=aws_iam.ServicePrincipal("cloudformation.amazonaws.com"),
            description="CloudFormation Role",
            inline_policies={
                "admin-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            resources=["*"],
                            actions=["*"],
                        ),
                    ]
                )
            },
        )
