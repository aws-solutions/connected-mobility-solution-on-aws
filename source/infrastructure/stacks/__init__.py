# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
from dataclasses import dataclass

# Third Party Libraries
from aws_cdk import ArnFormat, Stack, aws_iam
from constructs import Construct


# pylint: disable=invalid-name
@dataclass(frozen=True)
class CmsConstantsClass:
    STAGE: str = os.environ.get("STAGE", "dev")
    APP_NAME: str = "cms"
    STACK_NAME: str = f"cms-{STAGE}"
    MODULE_NAME: str = f"Connected-mobility-solution-on-aws-{STAGE}"
    SOLUTION_NAME: str = "Connected Mobility Solution on AWS"
    SOLUTION_ID: str = "SO0241"
    SOLUTION_VERSION: str = "v1.0.1"
    APPLICATION_TYPE: str = "AWS-Solutions"
    USER_AGENT_STRING: str = f"AWSSOLUTION/{SOLUTION_ID}/{SOLUTION_VERSION}"


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


CmsConstants = CmsConstantsClass()
