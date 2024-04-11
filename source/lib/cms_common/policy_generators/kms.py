# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0


# AWS Libraries
from aws_cdk import ArnFormat, Stack, aws_iam
from constructs import Construct


def generate_kms_policy_statement(
    self: Construct, kms_encryption_key_id: str, allow_encrypt: bool
) -> aws_iam.PolicyStatement:
    policy_permissions = ["kms:Decrypt"]
    encrypt_permissions = ["kms:Encrypt", "kms:GenerateDataKey"]
    if allow_encrypt:
        policy_permissions.extend(encrypt_permissions)
    return aws_iam.PolicyStatement(
        effect=aws_iam.Effect.ALLOW,
        actions=policy_permissions,
        resources=[
            Stack.of(self).format_arn(
                service="kms",
                resource="key",
                resource_name=f"{kms_encryption_key_id}",
                arn_format=ArnFormat.SLASH_RESOURCE_NAME,
            ),
        ],
    )
