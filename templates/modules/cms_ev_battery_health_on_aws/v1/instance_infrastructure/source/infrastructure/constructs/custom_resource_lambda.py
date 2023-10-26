# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library

# Third Party Libraries
from aws_cdk import Duration, aws_iam, aws_lambda, aws_logs
from constructs import Construct

# Connected Mobility Solution on AWS
from ...config.constants import EVBatteryHealthConstants
from ..lib.policy_generators import generate_lambda_cloudwatch_logs_policy_document


class CustomResourceLambdaConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        dependency_layer: aws_lambda.LayerVersion,
    ) -> None:
        super().__init__(scope, construct_id)

        custom_resource_lambda_function_name = (
            f"{EVBatteryHealthConstants.APP_NAME}-custom-resource-lambda"
        )

        self.custom_resource_lambda_role = aws_iam.Role(
            self,
            "lambda-role",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            inline_policies={
                "cloudwatch-policy": generate_lambda_cloudwatch_logs_policy_document(
                    self, lambda_function_name=custom_resource_lambda_function_name
                ),
            },
        )

        self.custom_resource_lambda = aws_lambda.Function(
            self,
            "lambda-function",
            description="CMS EV battery health custom resource lambda function",
            handler="custom_resource.main.handler",
            function_name=custom_resource_lambda_function_name,
            runtime=aws_lambda.Runtime.PYTHON_3_10,
            code=aws_lambda.Code.from_asset("source/handlers"),
            timeout=Duration.seconds(60),
            role=self.custom_resource_lambda_role,
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
            layers=[dependency_layer],
            environment={
                "USER_AGENT_STRING": EVBatteryHealthConstants.USER_AGENT_STRING,
            },
        )

    def add_policy_to_custom_resource_lambda(self, policy: aws_iam.Policy) -> None:
        self.custom_resource_lambda_role.attach_inline_policy(policy)
