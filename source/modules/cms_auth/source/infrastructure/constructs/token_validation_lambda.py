# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library

# AWS Libraries
from aws_cdk import Duration, Stack, aws_ec2, aws_iam, aws_lambda, aws_logs
from constructs import Construct

# CMS Common Library
from cms_common.config.resource_names import (
    ResourceName,
    ResourcePrefix,
    remove_leading_slash,
)
from cms_common.config.ssm import resolve_ssm_parameter
from cms_common.config.stack_inputs import SolutionConfigInputs
from cms_common.constructs.vpc_construct import VpcConstruct
from cms_common.policy_generators.cloudwatch import (
    generate_lambda_cloudwatch_logs_policy_document,
)
from cms_common.policy_generators.ec2_vpc import generate_ec2_vpc_policy
from cms_common.resource_names.auth import AuthSetupResourceNames


class TokenValidationLambdaConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        dependency_layer: aws_lambda.LayerVersion,
        identity_provider_id: str,
        app_unique_id: str,
        solution_config_inputs: SolutionConfigInputs,
        vpc_construct: VpcConstruct,
    ) -> None:
        super().__init__(scope, construct_id)

        auth_setup_resource_names = AuthSetupResourceNames.from_identity_provider_id(
            identity_provider_id
        )

        lambda_function_name = ResourceName.hyphen_separated(
            prefix=ResourcePrefix.hyphen_separated(
                app_unique_id=app_unique_id,
                module_name=solution_config_inputs.module_short_name,
            ),
            name="token-validation",
        )
        lambda_role = aws_iam.Role(
            self,
            "lambda-role",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            path="/",
            inline_policies={
                "cloudwatch": generate_lambda_cloudwatch_logs_policy_document(
                    self, lambda_function_name=lambda_function_name
                ),
                "secretsmanager": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=["secretsmanager:GetSecretValue"],
                            resources=[
                                resolve_ssm_parameter(
                                    auth_setup_resource_names.idp_config_secret_arn_ssm_parameter
                                )
                            ],
                        )
                    ]
                ),
                "ssm": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=["ssm:GetParameter"],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="ssm",
                                    resource="parameter",
                                    resource_name=remove_leading_slash(
                                        auth_setup_resource_names.idp_config_secret_arn_ssm_parameter
                                    ),  # Leading slash must not be present on SSM IAM permissions
                                ),
                            ],
                        ),
                    ]
                ),
                "ec2-vpc-policy": generate_ec2_vpc_policy(
                    self,
                    vpc_construct=vpc_construct,
                    subnet_selection=vpc_construct.private_subnet_selection,
                    authorized_service="lambda.amazonaws.com",
                ),
            },
        )

        self.lambda_function = aws_lambda.Function(
            self,
            "lambda-function",
            description="CMS Token Validation Lambda Function",
            handler="function.main.handler",
            function_name=lambda_function_name,
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            code=aws_lambda.Code.from_asset(
                "deployment/dist/lambda/token_validation_lambda.zip"
            ),
            timeout=Duration.seconds(60),
            role=lambda_role,
            layers=[dependency_layer],
            environment={
                "IDENTITY_PROVIDER_ID": identity_provider_id,
                "USER_AGENT_STRING": solution_config_inputs.get_user_agent_string(),
            },
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
