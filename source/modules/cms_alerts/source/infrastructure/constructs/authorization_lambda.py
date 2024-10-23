# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any

# AWS Libraries
from aws_cdk import Duration, aws_ec2, aws_iam, aws_lambda, aws_logs
from constructs import Construct

# CMS Common Library
from cms_common.config.resource_names import ResourceName, ResourcePrefix
from cms_common.config.stack_inputs import SolutionConfigInputs
from cms_common.constructs.vpc_construct import VpcConstruct
from cms_common.policy_generators.cloudwatch import (
    generate_lambda_cloudwatch_logs_policy_document,
)
from cms_common.policy_generators.ec2_vpc import generate_ec2_vpc_policy


class AuthorizationLambdaConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_unique_id: str,
        solution_config_inputs: SolutionConfigInputs,
        dependency_layer: aws_lambda.LayerVersion,
        token_validation_lambda_arn: str,
        vpc_construct: VpcConstruct,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        authorization_lambda_name = ResourceName.hyphen_separated(
            prefix=ResourcePrefix.hyphen_separated(
                app_unique_id=app_unique_id,
                module_name=solution_config_inputs.module_short_name,
            ),
            name="authorization",
        )

        self.authorization_lambda = aws_lambda.Function(
            self,
            "authorization-lambda",
            function_name=authorization_lambda_name,
            code=aws_lambda.Code.from_asset("dist/lambda/authorization.zip"),
            description="CMS Alerts Authorization Function",
            environment={
                "USER_AGENT_STRING": solution_config_inputs.get_user_agent_string(),
                "TOKEN_VALIDATION_LAMBDA_ARN": token_validation_lambda_arn,
            },
            handler="main.handler",
            runtime=aws_lambda.Runtime.PYTHON_3_12,
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
                    "ec2-policy": generate_ec2_vpc_policy(
                        self,
                        vpc_construct=vpc_construct,
                        subnet_selection=vpc_construct.private_subnet_selection,
                        authorized_service="lambda.amazonaws.com",
                    ),
                },
            ),
            layers=[dependency_layer],
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
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
        )
