# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# AWS Libraries
from aws_cdk import Stack, aws_iam, aws_kms, aws_logs
from constructs import Construct


class CMKEncryptedLogGroupConstruct(Construct):
    def __init__(self, scope: Construct, construct_id: str) -> None:
        super().__init__(scope, construct_id)

        log_group_kms_key = aws_kms.Key(
            self,
            "log-group-key",
            enable_key_rotation=True,
        )

        log_group_kms_key.add_to_resource_policy(
            statement=aws_iam.PolicyStatement(
                effect=aws_iam.Effect.ALLOW,
                principals=[
                    aws_iam.ServicePrincipal(
                        f"logs.{Stack.of(self).region}.amazonaws.com"
                    )
                ],
                actions=[
                    "kms:Encrypt",
                    "kms:Decrypt",
                    "kms:GenerateDataKey",
                ],
                resources=["*"],
            )
        )

        self.log_group = aws_logs.LogGroup(
            self,
            "log-group",
            encryption_key=log_group_kms_key,
            retention=aws_logs.RetentionDays.THREE_MONTHS,
        )
