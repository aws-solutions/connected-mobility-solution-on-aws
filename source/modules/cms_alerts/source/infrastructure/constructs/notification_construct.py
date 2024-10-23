# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any

# AWS Libraries
from aws_cdk import (
    Duration,
    Stack,
    aws_dynamodb,
    aws_ec2,
    aws_iam,
    aws_kms,
    aws_lambda,
    aws_lambda_destinations,
    aws_logs,
    aws_sqs,
)
from constructs import Construct

# CMS Common Library
from cms_common.config.resource_names import ResourceName, ResourcePrefix
from cms_common.config.stack_inputs import SolutionConfigInputs
from cms_common.constructs.vpc_construct import VpcConstruct
from cms_common.policy_generators.cloudwatch import (
    generate_lambda_cloudwatch_logs_policy_document,
)
from cms_common.policy_generators.ec2_vpc import generate_ec2_vpc_policy
from cms_common.policy_generators.kms import generate_kms_policy_statement_from_key_id


class NotificationConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_unique_id: str,
        solution_config_inputs: SolutionConfigInputs,
        dependency_layer: aws_lambda.LayerVersion,
        deployment_uuid: str,
        user_subscription_topic_general_key_id: str,
        sns_topic_prefix: str,
        vpc_construct: VpcConstruct,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        notifications_lambda_name = ResourceName.hyphen_separated(
            prefix=ResourcePrefix.hyphen_separated(
                app_unique_id=app_unique_id,
                module_name=solution_config_inputs.module_short_name,
            ),
            name="send-notifications",
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
                                    resource=f"{sns_topic_prefix}-*",
                                )
                            ],
                        ),
                        generate_kms_policy_statement_from_key_id(
                            self, user_subscription_topic_general_key_id, True
                        ),
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
                        ),
                        generate_kms_policy_statement_from_key_id(
                            self, self.notifications_table_key.key_id, False
                        ),
                    ]
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
                        ),
                        generate_kms_policy_statement_from_key_id(
                            self, dead_letter_queue_key.key_id, False
                        ),
                    ]
                ),
                "ec2-policy": generate_ec2_vpc_policy(
                    self,
                    vpc_construct=vpc_construct,
                    subnet_selection=vpc_construct.private_subnet_selection,
                    authorized_service="lambda.amazonaws.com",
                ),
            },
        )

        self.send_notifications_lambda = aws_lambda.Function(
            self,
            "send-notifications-lambda",
            function_name=notifications_lambda_name,
            code=aws_lambda.Code.from_asset("dist/lambda/send_notifications.zip"),
            description="CMS Alerts Notifications Lambda Function",
            environment={
                "USER_AGENT_STRING": solution_config_inputs.get_user_agent_string(),
                "DEPLOYMENT_UUID": deployment_uuid,
            },
            handler="app.main.handler",
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            timeout=Duration.minutes(1),
            role=aws_iam.Role.without_policy_updates(send_notifications_lambda_role),
            layers=[dependency_layer],
            vpc=vpc_construct.vpc,
            vpc_subnets=vpc_construct.private_subnet_selection,
            security_groups=[
                aws_ec2.SecurityGroup(
                    self,
                    "security-group",
                    vpc=vpc_construct.vpc,
                    allow_all_outbound=True,  # NOSONAR
                )
            ],
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
