# -*- coding: utf-8 -*-

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
# Standard Library
from typing import List

# Third Party Libraries
from aws_cdk import ArnFormat, Aws, Fn, Stack, aws_iam, aws_ssm
from constructs import Construct

GUID_LENGTH = 36


def fetch_ssm_parameter(
    scope: Construct, param_id: str, string_parameter_name: str
) -> str:
    return aws_ssm.StringParameter.from_string_parameter_name(
        scope,
        param_id,
        string_parameter_name,
    ).string_value


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
            )
        ]
    )


# Generates a physical id, shorter than max_length, with an appended unique stack identifier. Format: <prefix><all_substrings>-<stack_id_guid>
def generate_physical_name(
    scope: Construct,
    prefix: str,
    physical_name_substrings: List[str],
    max_length: int,
) -> str:
    prefix_length = len(prefix)
    max_parts_length = (
        max_length - prefix_length - 1 - GUID_LENGTH
    )  # 1 is for the hyphen, GUID_LENGTH is for the GUID fetched from the stack_id for this scope's stack

    unique_stack_id_part = Fn.select(2, Fn.split("/", Stack.of(scope).stack_id))

    all_substrings = "".join(physical_name_substrings)

    if len(all_substrings) > max_parts_length:
        substring_length = max_parts_length // 2
        all_substrings = (
            all_substrings[:substring_length]
            + all_substrings[len(all_substrings) - substring_length :]
        )

    return prefix.lower() + all_substrings + "-" + unique_stack_id_part
