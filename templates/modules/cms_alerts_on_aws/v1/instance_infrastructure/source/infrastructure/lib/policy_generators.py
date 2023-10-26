# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library

# Third Party Libraries
from aws_cdk import ArnFormat, Stack, aws_iam
from constructs import Construct


def generate_lambda_cloudwatch_logs_policy_document(
    self: Construct, lambda_function_name: str
) -> aws_iam.PolicyDocument:
    return aws_iam.PolicyDocument(
        statements=[
            aws_iam.PolicyStatement(
                effect=aws_iam.Effect.ALLOW,
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                ],
                resources=[
                    Stack.of(self).format_arn(
                        service="logs",
                        resource="log-group",
                        resource_name=f"/aws/lambda/{lambda_function_name}",
                        arn_format=ArnFormat.COLON_RESOURCE_NAME,
                    ),
                    Stack.of(self).format_arn(
                        service="logs",
                        resource="log-group",
                        resource_name=f"/aws/lambda/{lambda_function_name}:log-stream:*",
                        arn_format=ArnFormat.COLON_RESOURCE_NAME,
                    ),
                ],
            ),
        ]
    )


def generate_kms_policy_document(
    self: Construct, kms_encryption_key_id: str, allow_encrypt: bool
) -> aws_iam.PolicyDocument:
    policy_permissions = ["kms:Decrypt"]
    encrypt_permissions = ["kms:Encrypt", "kms:GenerateDataKey"]
    if allow_encrypt:
        policy_permissions.extend(encrypt_permissions)
    return aws_iam.PolicyDocument(
        statements=[
            aws_iam.PolicyStatement(
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
        ]
    )
