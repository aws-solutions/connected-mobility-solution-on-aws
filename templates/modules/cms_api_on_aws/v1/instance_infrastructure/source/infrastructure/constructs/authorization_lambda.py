# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
from aws_cdk import Duration, aws_iam, aws_lambda, aws_logs
from constructs import Construct

# Connected Mobility Solution on AWS
from ...config.constants import APIConstants
from ..lib.policy_generators import generate_lambda_cloudwatch_logs_policy_document


class AuthorizationLambdaConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        dependency_layer: aws_lambda.LayerVersion,
        token_validation_lambda_arn: str,
        token_use: str,
    ) -> None:
        super().__init__(scope, construct_id)

        authorization_lambda_function_name = (
            f"{APIConstants.APP_NAME}-authorization-lambda"
        )
        authorization_lambda_role = aws_iam.Role(
            self,
            "lambda-role",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            path="/",
            inline_policies={
                "cloudwatch-policy": generate_lambda_cloudwatch_logs_policy_document(
                    self, lambda_function_name=authorization_lambda_function_name
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
        )

        self.authorization_lambda = aws_lambda.Function(
            self,
            "lambda-function",
            description="CMS API authorization lambda function",
            handler="authorization.main.handler",
            function_name=authorization_lambda_function_name,
            runtime=aws_lambda.Runtime.PYTHON_3_10,
            code=aws_lambda.Code.from_asset("source/handlers"),
            timeout=Duration.seconds(60),
            role=authorization_lambda_role,
            layers=[dependency_layer],
            environment={
                "USER_AGENT_STRING": APIConstants.USER_AGENT_STRING,
                "TOKEN_USE": token_use,
                "TOKEN_VALIDATION_LAMBDA_ARN": token_validation_lambda_arn,
            },
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
        )
