# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any

# AWS Libraries
from aws_cdk import (
    ArnFormat,
    Duration,
    Stack,
    aws_iam,
    aws_kms,
    aws_lambda_event_sources,
    aws_sns,
    aws_sqs,
)
from aws_solutions_constructs.aws_sns_sqs import SnsToSqs
from aws_solutions_constructs.aws_sqs_lambda import SqsToLambda
from constructs import Construct

# CMS Common Library
from cms_common.config.resource_names import ResourceName, ResourcePrefix
from cms_common.config.stack_inputs import SolutionConfigInputs

# Connected Mobility Solution on AWS
from .incoming_alerts_construct import IncomingAlertsConstruct


class SnsToSqsToLambdaConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_unique_id: str,
        solution_config_inputs: SolutionConfigInputs,
        incoming_alerts_construct: IncomingAlertsConstruct,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.sns_topic_key = aws_kms.Key(
            self,
            "sns-topic-key",
            enable_key_rotation=True,
        )

        self.sns_topic = aws_sns.Topic(
            self,
            "sns-topic",
            display_name=ResourceName.hyphen_separated(
                prefix=ResourcePrefix.hyphen_separated(
                    app_unique_id=app_unique_id,
                    module_name=solution_config_inputs.module_short_name,
                ),
                name="topic",
            ),
            fifo=False,
            master_key=self.sns_topic_key,
        )

        sqs_queue_key = aws_kms.Key(
            self,
            "sqs-queue-key",
            enable_key_rotation=True,
        )

        dead_letter_queue = aws_sqs.Queue(
            self,
            "dead-letter-queue",
            encryption=aws_sqs.QueueEncryption.KMS,
            encryption_master_key=sqs_queue_key,
            enforce_ssl=True,
        )

        self.sqs_queue = aws_sqs.Queue(
            self,
            "sqs-queue",
            encryption=aws_sqs.QueueEncryption.KMS,
            encryption_master_key=sqs_queue_key,
            visibility_timeout=Duration.seconds(31),
            dead_letter_queue=aws_sqs.DeadLetterQueue(
                max_receive_count=1, queue=dead_letter_queue
            ),
            enforce_ssl=True,
        )

        incoming_alerts_construct.add_to_alerts_lambda_role_policy(
            effect=aws_iam.Effect.ALLOW,
            actions=[
                "sqs:DeleteMessage",
                "sqs:GetQueueAttributes",
                "sqs:ReceiveMessage",
            ],
            resources=[self.sqs_queue.queue_arn],
        )

        incoming_alerts_construct.add_to_alerts_lambda_role_policy(
            effect=aws_iam.Effect.ALLOW,
            actions=["kms:Decrypt"],
            resources=[
                Stack.of(self).format_arn(
                    service="kms",
                    resource="key",
                    resource_name=f"{sqs_queue_key.key_id}",
                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                ),
            ],
        )

        SnsToSqs(
            self,
            "sns-to-sqs",
            existing_queue_obj=self.sqs_queue,
            existing_topic_obj=self.sns_topic,
        )

        SqsToLambda(
            self,
            "sqs-to-lambda",
            existing_lambda_obj=incoming_alerts_construct.alerts_lambda,
            existing_queue_obj=self.sqs_queue,
            sqs_event_source_props=aws_lambda_event_sources.SqsEventSourceProps(
                batch_size=1,
            ),
        )
