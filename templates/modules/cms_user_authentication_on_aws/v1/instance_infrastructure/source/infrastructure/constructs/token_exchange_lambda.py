# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
from aws_cdk import Duration, aws_iam, aws_lambda, aws_logs
from constructs import Construct

# Connected Mobility Solution on AWS
from ...config.constants import UserAuthenticationConstants
from ..lib.policy_generators import generate_lambda_cloudwatch_logs_policy_document


class TokenExchangeLambdaConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        dependency_layer: aws_lambda.LayerVersion,
        user_client_id: str,
        user_client_secret_arn: str,
        redirect_uri: str,
        domain_prefix: str,
        user_pool_region: str,
        token_validation_lambda_arn: str,
    ) -> None:
        super().__init__(scope, construct_id)

        lambda_function_name = f"{UserAuthenticationConstants.APP_NAME}-token-exchange"
        lambda_role = aws_iam.Role(
            self,
            "lambda-role",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            path="/",
            inline_policies={
                "cloudwatch": generate_lambda_cloudwatch_logs_policy_document(
                    self, lambda_function_name=lambda_function_name
                ),
                "lambda": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=["lambda:InvokeFunction"],
                            resources=[token_validation_lambda_arn],
                        )
                    ]
                ),
                "secretsmanager": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=["secretsmanager:GetSecretValue"],
                            resources=[user_client_secret_arn],
                        )
                    ]
                ),
            },
        )

        self.lambda_function = aws_lambda.Function(
            self,
            "lambda-function",
            description="CMS Token Exchange Lambda Function",
            handler="token_exchange_lambda.main.handler",
            function_name=lambda_function_name,
            runtime=aws_lambda.Runtime.PYTHON_3_10,
            code=aws_lambda.Code.from_asset("source/handlers"),
            timeout=Duration.seconds(60),
            role=lambda_role,
            layers=[dependency_layer],
            environment={
                "USER_AGENT_STRING": UserAuthenticationConstants.USER_AGENT_STRING,
                "USER_CLIENT_ID": user_client_id,
                "USER_CLIENT_SECRET_ARN": user_client_secret_arn,
                "REDIRECT_URI": redirect_uri,
                "DOMAIN_PREFIX": domain_prefix,
                "USER_POOL_REGION": user_pool_region,
                "TOKEN_VALIDATION_LAMBDA_ARN": token_validation_lambda_arn,
            },
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
        )
