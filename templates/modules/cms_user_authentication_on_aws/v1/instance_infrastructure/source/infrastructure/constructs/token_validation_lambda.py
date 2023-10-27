# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
# Third Party Libraries
from aws_cdk import Duration, Stack, aws_iam, aws_lambda, aws_logs
from constructs import Construct

# Connected Mobility Solution on AWS
from ...config.constants import UserAuthenticationConstants
from ..lib.policy_generators import generate_lambda_cloudwatch_logs_policy_document


class TokenValidationLambdaConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        dependency_layer: aws_lambda.LayerVersion,
        user_pool_id: str,
        user_client_id: str,
        service_client_id: str,
        formatted_cms_service_scope: str,
    ) -> None:
        super().__init__(scope, construct_id)

        lambda_function_name = (
            f"{UserAuthenticationConstants.APP_NAME}-token-validation-lambda"
        )
        lambda_role = aws_iam.Role(
            self,
            "lambda-role",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            path="/",
            inline_policies={
                "cloudwatch-policy": generate_lambda_cloudwatch_logs_policy_document(
                    self, lambda_function_name=lambda_function_name
                ),
            },
        )

        self.lambda_function = aws_lambda.Function(
            self,
            "lambda-function",
            description="CMS Token Validation Lambda Function",
            handler="token_validation_lambda.main.handler",
            function_name=lambda_function_name,
            runtime=aws_lambda.Runtime.PYTHON_3_10,
            code=aws_lambda.Code.from_asset("source/handlers"),
            timeout=Duration.seconds(60),
            role=lambda_role,
            layers=[dependency_layer],
            environment={
                "USER_AGENT_STRING": UserAuthenticationConstants.USER_AGENT_STRING,
                "USER_POOL_REGION": Stack.of(self).region,
                "USER_POOL_ID": user_pool_id,
                "USER_CLIENT_ID": user_client_id,
                "SERVICE_CLIENT_ID": service_client_id,
                "FORMATTED_CMS_SERVICE_SCOPE": formatted_cms_service_scope,
            },
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
        )
