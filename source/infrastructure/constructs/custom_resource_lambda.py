# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
from aws_cdk import Duration, aws_iam, aws_lambda, aws_logs
from constructs import Construct

# Connected Mobility Solution on AWS
from ..stacks import CmsConstants, generate_lambda_cloudwatch_logs_policy_document


class CustomResourceLambdaConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        dependency_layer: aws_lambda.LayerVersion,
    ) -> None:
        super().__init__(scope, construct_id)
        custom_resource_lambda_name = f"{CmsConstants.STACK_NAME}-custom-resource"

        self.custom_resource_lambda_role = aws_iam.Role(
            self,
            "lambda-role",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            inline_policies={
                "lambda-logs-policy": generate_lambda_cloudwatch_logs_policy_document(
                    self, custom_resource_lambda_name
                ),
            },
        )

        self.custom_resource_lambda = aws_lambda.Function(
            self,
            "lambda-function",
            code=aws_lambda.Code.from_asset(
                "source/infrastructure/handlers/custom_resource"
            ),
            handler="custom_resource.handler",
            function_name=custom_resource_lambda_name,
            role=self.custom_resource_lambda_role,
            runtime=aws_lambda.Runtime.PYTHON_3_10,
            timeout=Duration.minutes(5),
            layers=[dependency_layer],
            environment={"USER_AGENT_STRING": CmsConstants.USER_AGENT_STRING},
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
        )

    def add_policy_to_custom_resource_lambda(self, policy: aws_iam.Policy) -> None:
        self.custom_resource_lambda_role.attach_inline_policy(policy)
