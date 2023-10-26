# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json
from typing import Any

# Third Party Libraries
from aws_cdk import (
    Duration,
    Stack,
    aws_dynamodb,
    aws_iam,
    aws_kms,
    aws_lambda,
    aws_logs,
)
from constructs import Construct

# Connected Mobility Solution on AWS
from ...config.constants import AlertsConstants
from ..lib.policy_generators import (
    generate_kms_policy_document,
    generate_lambda_cloudwatch_logs_policy_document,
)


class UserSubscriptionsConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        dependency_layer: aws_lambda.LayerVersion,
        deployment_uuid: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        user_subscriptions_lambda_name = (
            f"{AlertsConstants.APP_NAME}-user-subscriptions-lambda"
        )

        self.user_subscription_topic_general_key = aws_kms.Key(
            self, "user_subscription_topic_general_key", enable_key_rotation=True
        )

        self.user_email_subscriptions_table_key = aws_kms.Key(
            self,
            "user-subscriptions-table-key",
            enable_key_rotation=True,
        )

        self.user_email_subscriptions_table = aws_dynamodb.Table(
            self,
            "user-email-subscriptions-table",
            billing_mode=aws_dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=aws_dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.user_email_subscriptions_table_key,
            partition_key={
                "name": "email",
                "type": aws_dynamodb.AttributeType.STRING,
            },
            sort_key={
                "name": "topic_key",
                "type": aws_dynamodb.AttributeType.STRING,
            },
            point_in_time_recovery=True,
        )

        self.user_subscriptions_lambda = aws_lambda.Function(
            self,
            "user-subscriptions-lambda",
            function_name=user_subscriptions_lambda_name,
            code=aws_lambda.Code.from_asset("source/handlers"),
            description="CMS Alerts User Subscriptions Function",
            environment={
                "USER_AGENT_STRING": AlertsConstants.USER_AGENT_STRING,
                "USER_EMAIL_SUBSCRIPTIONS_TABLE": self.user_email_subscriptions_table.table_name,
                "ALARM_TYPES": json.dumps(
                    [
                        "VEHICLE_ALARM",
                        "EV_BATTERY_HEALTH_ALARM",
                    ]
                ),
                "SNS_TOPIC_PREFIX": AlertsConstants.SNS_TOPIC_PREFIX,
                "SNS_TOPIC_GENERAL_KEY_ID": self.user_subscription_topic_general_key.key_id,
                "DEPLOYMENT_UUID": deployment_uuid,
            },
            handler="user_subscriptions.main.handler",
            runtime=aws_lambda.Runtime.PYTHON_3_10,
            timeout=Duration.minutes(1),
            role=aws_iam.Role(
                self,
                "user-subscriptions-lambda-role",
                assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
                inline_policies={
                    "sns-policy": aws_iam.PolicyDocument(
                        statements=[
                            aws_iam.PolicyStatement(
                                effect=aws_iam.Effect.ALLOW,
                                actions=[
                                    "sns:Subscribe",
                                    "sns:Unsubscribe",
                                    "sns:CreateTopic",
                                    "sns:TagResource",
                                ],
                                resources=[
                                    Stack.of(self).format_arn(
                                        service="sns",
                                        resource=f"{AlertsConstants.SNS_TOPIC_PREFIX}-*",
                                    )
                                ],
                            )
                        ]
                    ),
                    "cloudwatch-policy": generate_lambda_cloudwatch_logs_policy_document(
                        self, user_subscriptions_lambda_name
                    ),
                    "dynamodb-policy": aws_iam.PolicyDocument(
                        statements=[
                            aws_iam.PolicyStatement(
                                effect=aws_iam.Effect.ALLOW,
                                actions=[
                                    "dynamodb:PutItem",
                                    "dynamodb:GetItem",
                                    "dynamodb:DeleteItem",
                                    "dynamodb:Query",
                                    "dynamodb:BatchWriteItem",
                                ],
                                resources=[
                                    self.user_email_subscriptions_table.table_arn
                                ],
                            )
                        ]
                    ),
                    "kms-subs-table-key-policy": generate_kms_policy_document(
                        self, self.user_email_subscriptions_table_key.key_id, True
                    ),
                },
            ),
            layers=[dependency_layer],
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
        )

        self.user_subscriptions_lambda.grant_invoke(
            aws_iam.ServicePrincipal("appsync.amazonaws.com")
        )
