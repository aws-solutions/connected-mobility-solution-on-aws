# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json
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
    aws_logs,
)
from constructs import Construct

# CMS Common Library
from cms_common.config.resource_names import ResourceName, ResourcePrefix
from cms_common.config.stack_inputs import SolutionConfigInputs
from cms_common.constructs.vpc_construct import VpcConstruct
from cms_common.policy_generators.ec2_vpc import generate_ec2_vpc_policy

# Connected Mobility Solution on AWS
from ..lib.policy_generators import (
    generate_kms_policy_document,
    generate_lambda_cloudwatch_logs_policy_document,
)


class UserSubscriptionsConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_unique_id: str,
        solution_config_inputs: SolutionConfigInputs,
        dependency_layer: aws_lambda.LayerVersion,
        deployment_uuid: str,
        sns_topic_prefix: str,
        vpc_construct: VpcConstruct,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        user_subscriptions_lambda_name = ResourceName.hyphen_separated(
            prefix=ResourcePrefix.hyphen_separated(
                app_unique_id=app_unique_id,
                module_name=solution_config_inputs.module_short_name,
            ),
            name="user-subscriptions",
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
            code=aws_lambda.Code.from_asset("dist/lambda/user_subscriptions.zip"),
            description="CMS Alerts User Subscriptions Function",
            environment={
                "USER_AGENT_STRING": solution_config_inputs.get_user_agent_string(),
                "USER_EMAIL_SUBSCRIPTIONS_TABLE": self.user_email_subscriptions_table.table_name,
                "ALARM_TYPES": json.dumps(
                    [
                        "VEHICLE_ALARM",
                        "EV_BATTERY_HEALTH_ALARM",
                    ]
                ),
                "SNS_TOPIC_PREFIX": sns_topic_prefix,
                "SNS_TOPIC_GENERAL_KEY_ID": self.user_subscription_topic_general_key.key_id,
                "DEPLOYMENT_UUID": deployment_uuid,
            },
            handler="app.main.handler",
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
                                        resource=f"{sns_topic_prefix}-*",
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
                    "ec2-policy": generate_ec2_vpc_policy(
                        self,
                        vpc_construct=vpc_construct,
                        subnet_selection=vpc_construct.private_subnet_selection,
                        authorized_service="lambda.amazonaws.com",
                    ),
                },
            ),
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

        self.user_subscriptions_lambda.grant_invoke(
            aws_iam.ServicePrincipal("appsync.amazonaws.com")
        )
