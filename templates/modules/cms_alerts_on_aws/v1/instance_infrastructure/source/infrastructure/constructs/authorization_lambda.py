# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any

# Third Party Libraries
from aws_cdk import Duration, aws_iam, aws_lambda, aws_logs
from constructs import Construct

# Connected Mobility Solution on AWS
from ...config.constants import AlertsConstants
from ..lib.policy_generators import generate_lambda_cloudwatch_logs_policy_document


class AuthorizationLambdaConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        dependency_layer: aws_lambda.LayerVersion,
        token_validation_lambda_arn: str,
        token_use: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        authorization_lambda_name = f"{AlertsConstants.APP_NAME}-authorization-lambda"

        self.authorization_lambda = aws_lambda.Function(
            self,
            "authorization-lambda",
            function_name=authorization_lambda_name,
            code=aws_lambda.Code.from_asset("source/handlers"),
            description="CMS Alerts Authorization Function",
            environment={
                "USER_AGENT_STRING": AlertsConstants.USER_AGENT_STRING,
                "TOKEN_USE": token_use,
                "TOKEN_VALIDATION_LAMBDA_ARN": token_validation_lambda_arn,
            },
            handler="authorization.main.handler",
            runtime=aws_lambda.Runtime.PYTHON_3_10,
            timeout=Duration.minutes(1),
            role=aws_iam.Role(
                self,
                "authorization-lambda-role",
                assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
                inline_policies={
                    "cloudwatch-policy": generate_lambda_cloudwatch_logs_policy_document(
                        self, lambda_function_name=authorization_lambda_name
                    ),
                    "lambda-policy": aws_iam.PolicyDocument(
                        statements=[
                            aws_iam.PolicyStatement(
                                effect=aws_iam.Effect.ALLOW,
                                actions=["lambda:InvokeFunction"],
                                resources=[token_validation_lambda_arn],
                            )
                        ]
                    ),
                },
            ),
            layers=[dependency_layer],
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
        )
