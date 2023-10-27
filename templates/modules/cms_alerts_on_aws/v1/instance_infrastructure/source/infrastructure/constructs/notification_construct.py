# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any

# Third Party Libraries
from aws_cdk import (
    Duration,
    Stack,
    aws_dynamodb,
    aws_iam,
    aws_kms,
    aws_lambda,
    aws_lambda_destinations,
    aws_logs,
    aws_sqs,
)
from constructs import Construct

# Connected Mobility Solution on AWS
from ...config.constants import AlertsConstants
from ..lib.policy_generators import (
    generate_kms_policy_document,
    generate_lambda_cloudwatch_logs_policy_document,
)


class NotificationConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        dependency_layer: aws_lambda.LayerVersion,
        deployment_uuid: str,
        user_subscription_topic_general_key_id: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        notifications_lambda_name = (
            f"{AlertsConstants.APP_NAME}-send-notifications-lambda"
        )

        self.notifications_table_key = aws_kms.Key(
            self,
            "notifications-table-key",
            enable_key_rotation=True,
        )

        dead_letter_queue_key = aws_kms.Key(
            self,
            "dlq-queue-key",
            enable_key_rotation=True,
        )

        dead_letter_queue = aws_sqs.Queue(
            self,
            "dead-letter-queue",
            encryption=aws_sqs.QueueEncryption.KMS,
            encryption_master_key=dead_letter_queue_key,
            enforce_ssl=True,
        )

        self.notifications_table = aws_dynamodb.Table(
            self,
            "notifications-table",
            billing_mode=aws_dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=aws_dynamodb.TableEncryption.CUSTOMER_MANAGED,
            encryption_key=self.notifications_table_key,
            partition_key={"name": "topic", "type": aws_dynamodb.AttributeType.STRING},
            sort_key={"name": "timestamp", "type": aws_dynamodb.AttributeType.STRING},
            point_in_time_recovery=True,
            stream=aws_dynamodb.StreamViewType.NEW_IMAGE,
        )

        send_notifications_lambda_role = aws_iam.Role(
            self,
            "notifications-lambda-role",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            inline_policies={
                "sns-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "sns:CreateTopic",
                                "sns:Publish",
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
                    self, notifications_lambda_name
                ),
                "dynamodb-stream-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "dynamodb:DescribeStream",
                                "dynamodb:GetRecords",
                                "dynamodb:GetShardIterator",
                            ],
                            resources=[
                                self.notifications_table.table_stream_arn  # type: ignore[list-item]
                            ],
                        )
                    ]
                ),
                "kms-notifications-table-key-policy": generate_kms_policy_document(
                    self, self.notifications_table_key.key_id, False
                ),
                "kms-dlq-key-policy": generate_kms_policy_document(
                    self, dead_letter_queue_key.key_id, False
                ),
                "kms-subs-topic-key-policy": generate_kms_policy_document(
                    self, user_subscription_topic_general_key_id, True
                ),
                "sqs-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "sqs:GetQueueAttributes",
                                "sqs:GetQueueUrl",
                                "sqs:SendMessage",
                            ],
                            resources=[dead_letter_queue.queue_arn],
                        )
                    ]
                ),
            },
        )

        self.send_notifications_lambda = aws_lambda.Function(
            self,
            "send-notifications-lambda",
            function_name=notifications_lambda_name,
            code=aws_lambda.Code.from_asset("source/handlers"),
            description="CMS Alerts Notifications Lambda Function",
            environment={
                "USER_AGENT_STRING": AlertsConstants.USER_AGENT_STRING,
                "DEPLOYMENT_UUID": deployment_uuid,
            },
            handler="send_notifications.main.handler",
            runtime=aws_lambda.Runtime.PYTHON_3_10,
            timeout=Duration.minutes(1),
            role=aws_iam.Role.without_policy_updates(send_notifications_lambda_role),
            layers=[dependency_layer],
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
        )

        aws_lambda.EventSourceMapping(
            self,
            "notifications-table-event-source-mapping",
            target=self.send_notifications_lambda,
            event_source_arn=self.notifications_table.table_stream_arn,
            starting_position=aws_lambda.StartingPosition.TRIM_HORIZON,
            batch_size=1,
            retry_attempts=3,
            on_failure=aws_lambda_destinations.SqsDestination(queue=dead_letter_queue),  # type: ignore[arg-type]
        )
