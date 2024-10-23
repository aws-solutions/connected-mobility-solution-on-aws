# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
# AWS Libraries
from aws_cdk import Stack, aws_iam
from constructs import Construct


class BedrockRoleConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_unique_id: str,
    ) -> None:
        super().__init__(scope, construct_id)

        self.role = aws_iam.Role(
            self,
            "iam-role",
            role_name=f"AmazonBedrockExecutionRoleForKnowledgeBase-{app_unique_id}-{Stack.of(self).region}",
            assumed_by=aws_iam.ServicePrincipal("bedrock.amazonaws.com"),
        )

    def attach_policy_to_role(self, policy: aws_iam.Policy) -> None:
        self.role.attach_inline_policy(policy)
