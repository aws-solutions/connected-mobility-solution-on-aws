# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any, List

# Third Party Libraries
from aws_cdk import ArnFormat, Duration, Stack, aws_iam, aws_lambda, aws_logs
from constructs import Construct

# Connected Mobility Solution on AWS
from ...config.constants import AlertsConstants
from ..lib.policy_generators import (
    generate_kms_policy_document,
    generate_lambda_cloudwatch_logs_policy_document,
)


class IncomingAlertsConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        dependency_layer: aws_lambda.LayerVersion,
        notifications_table_name: str,
        notifications_table_key_id: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        alerts_lambda_name = f"{AlertsConstants.APP_NAME}-create-alerts-lambda"

        self.alerts_lambda = aws_lambda.Function(
            self,
            "create-alerts-lambda",
            function_name=alerts_lambda_name,
            code=aws_lambda.Code.from_asset("source/handlers"),
            description="CMS Alerts Lambda Function",
            environment={
                "USER_AGENT_STRING": AlertsConstants.USER_AGENT_STRING,
                "NOTIFICATIONS_TABLE_NAME": notifications_table_name,
                "SNS_TOPIC_PREFIX": AlertsConstants.SNS_TOPIC_PREFIX,
            },
            handler="create_alerts.main.handler",
            runtime=aws_lambda.Runtime.PYTHON_3_10,
            timeout=Duration.seconds(30),
            role=aws_iam.Role(
                self,
                "alerts-lambda-role",
                assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
                inline_policies={
                    "cloudwatch-policy": generate_lambda_cloudwatch_logs_policy_document(
                        self, alerts_lambda_name
                    ),
                    "dynamodb-policy": aws_iam.PolicyDocument(
                        statements=[
                            aws_iam.PolicyStatement(
                                effect=aws_iam.Effect.ALLOW,
                                actions=[
                                    "dynamodb:PutItem",
                                ],
                                resources=[
                                    Stack.of(self).format_arn(
                                        service="dynamodb",
                                        resource="table",
                                        resource_name=f"{notifications_table_name}",
                                        arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                    ),
                                ],
                            )
                        ]
                    ),
                    "kms-policy-notifications-key": generate_kms_policy_document(
                        self, notifications_table_key_id, False
                    ),
                },
            ),
            layers=[dependency_layer],
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
        )

    def add_to_alerts_lambda_role_policy(
        self, effect: aws_iam.Effect, actions: List[str], resources: List[str]
    ) -> None:
        self.alerts_lambda.add_to_role_policy(
            statement=aws_iam.PolicyStatement(
                effect=effect, actions=actions, resources=resources
            )
        )
