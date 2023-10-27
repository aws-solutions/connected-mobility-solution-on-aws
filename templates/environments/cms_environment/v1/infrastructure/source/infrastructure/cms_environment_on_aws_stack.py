# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any

# Third Party Libraries
from aws_cdk import ArnFormat, Stack, aws_iam, aws_iot
from constructs import Construct


class CmsEnvironmentOnAwsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # This role will be used for IoT Core to send CloudWatch logs.
        iotcore_to_cloudwatch_role = aws_iam.Role(
            self,
            "iot-core-to-cloudwatch-role",
            assumed_by=aws_iam.ServicePrincipal("iot.amazonaws.com"),
            inline_policies={
                "cloud-watch-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "logs:CreateLogGroup",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents",
                                "logs:PutMetricFilter",
                                "logs:PutRetentionPolicy",
                            ],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="logs",
                                    resource="log-group",
                                    resource_name="*:log-stream:*",
                                    arn_format=ArnFormat.COLON_RESOURCE_NAME,
                                ),
                            ],
                        ),
                    ]
                )
            },
        )

        # Define IoT Core logging parameters.
        aws_iot.CfnLogging(
            self,
            "iot-core-logging",
            account_id=Stack.of(self).account,
            default_log_level="INFO",
            role_arn=iotcore_to_cloudwatch_role.role_arn,
        )
