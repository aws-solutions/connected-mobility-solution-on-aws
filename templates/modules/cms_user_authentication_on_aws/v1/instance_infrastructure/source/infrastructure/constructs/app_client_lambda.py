# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library

# Third Party Libraries
from aws_cdk import Duration, aws_iam, aws_lambda, aws_logs
from constructs import Construct

# Connected Mobility Solution on AWS
from ...config.constants import UserAuthenticationConstants
from ..lib.policy_generators import generate_lambda_cloudwatch_logs_policy_document


class AppClientLambdaConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        function_name: str,
        handler: str,
        action: str,
        dependency_layer: aws_lambda.LayerVersion,
        cognito_user_pool_id: str,
        cognito_user_pool_arn: str,
    ) -> None:
        super().__init__(scope, construct_id)

        lambda_role = aws_iam.Role(
            self,
            "lambda-role",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            path="/",
            inline_policies={
                "cloudwatch-logs-policy": generate_lambda_cloudwatch_logs_policy_document(
                    self, lambda_function_name=function_name
                ),
                "cognito-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                f"cognito-idp:{action}",
                            ],
                            resources=[
                                cognito_user_pool_arn,
                            ],
                        )
                    ]
                ),
            },
        )

        self.lambda_function = aws_lambda.Function(
            self,
            "lambda-function",
            function_name=function_name,
            code=aws_lambda.Code.from_asset("source/handlers"),
            description=f"User Authentication {action} Function",
            handler=handler,
            runtime=aws_lambda.Runtime.PYTHON_3_10,
            role=lambda_role,
            layers=[dependency_layer],
            timeout=Duration.seconds(60),
            environment={
                "COGNITO_USER_POOL_ID": cognito_user_pool_id,
                "USER_AGENT_STRING": UserAuthenticationConstants.USER_AGENT_STRING,
            },
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
        )
