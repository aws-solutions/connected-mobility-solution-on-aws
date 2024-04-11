# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library

# AWS Libraries
from aws_cdk import (
    ArnFormat,
    CustomResource,
    Duration,
    Stack,
    aws_ec2,
    aws_iam,
    aws_lambda,
    aws_logs,
)
from constructs import Construct

# CMS Common Library
from cms_common.config.resource_names import ResourceName, ResourcePrefix
from cms_common.config.stack_inputs import SolutionConfigInputs
from cms_common.constructs.custom_resource_lambda import CustomResourceLambdaConstruct
from cms_common.constructs.vpc_construct import VpcConstruct
from cms_common.policy_generators.cloudwatch import (
    generate_lambda_cloudwatch_logs_policy_document,
)
from cms_common.policy_generators.ec2_vpc import generate_ec2_vpc_policy

# Connected Mobility Solution on AWS
from ...handlers.custom_resource.function.lib.custom_resource_type_enum import (
    CustomResourceFunctionType,
)


class IoTCredentialsConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_unique_id: str,
        solution_config_inputs: SolutionConfigInputs,
        dependency_layer: aws_lambda.LayerVersion,
        custom_resource_lambda_construct: CustomResourceLambdaConstruct,
        claim_cert_provisioning_policy_name: str,
        vpc_construct: VpcConstruct,
    ) -> None:
        super().__init__(scope, construct_id)

        provisioning_secret_name = ResourceName.slash_separated(
            prefix=ResourcePrefix.slash_separated(
                app_unique_id=app_unique_id,
                module_name=solution_config_inputs.module_short_name,
            ),
            name="provisioning-credentials",
        )

        rotate_secret_lambda_function_name = ResourceName.hyphen_separated(
            prefix=ResourcePrefix.hyphen_separated(
                app_unique_id=app_unique_id,
                module_name=solution_config_inputs.module_short_name,
            ),
            name="rotate-secret",
        )

        rotate_secret_lambda_role = aws_iam.Role(
            self,
            "rotate-secret-lambda-role",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            path="/",
            inline_policies={
                "secrets-manager-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            actions=[
                                "secretsmanager:GetSecretValue",
                                "secretsmanager:PutSecretValue",
                                "secretsmanager:DescribeSecret",
                                "secretsmanager:UpdateSecretVersionStage",
                            ],
                            effect=aws_iam.Effect.ALLOW,
                            resources=[
                                Stack.of(self).format_arn(
                                    service="secretsmanager",
                                    resource="secret",
                                    resource_name=f"{provisioning_secret_name}*",
                                    arn_format=ArnFormat.COLON_RESOURCE_NAME,
                                ),
                            ],
                        ),
                    ]
                ),
                "iot-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            actions=[
                                "iot:UpdateCertificate",
                                "iot:DeleteCertificate",
                                "iot:ListAttachedPolicies",
                            ],
                            effect=aws_iam.Effect.ALLOW,
                            resources=[
                                Stack.of(self).format_arn(
                                    service="iot",
                                    resource="cert",
                                    resource_name="*",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                            ],
                        ),
                        aws_iam.PolicyStatement(
                            actions=[
                                "iot:AttachPolicy",
                                "iot:DetachPolicy",
                            ],
                            effect=aws_iam.Effect.ALLOW,
                            resources=[
                                Stack.of(self).format_arn(
                                    service="iot",
                                    resource="cert",
                                    resource_name="*",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                                Stack.of(self).format_arn(
                                    service="iot",
                                    resource="policy",
                                    resource_name=claim_cert_provisioning_policy_name,
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                            ],
                        ),
                        aws_iam.PolicyStatement(
                            actions=[
                                "iot:CreateKeysAndCertificate",
                                "iot:RegisterCertificateWithoutCA",
                            ],
                            effect=aws_iam.Effect.ALLOW,
                            resources=["*"],
                        ),
                    ]
                ),
                "cloudwatch-policy": generate_lambda_cloudwatch_logs_policy_document(
                    self, lambda_function_name=rotate_secret_lambda_function_name
                ),
                "ec2-vpc-policy": generate_ec2_vpc_policy(
                    self,
                    vpc_construct=vpc_construct,
                    subnet_selection=vpc_construct.private_subnet_selection,
                    authorized_service="lambda.amazonaws.com",
                ),
            },
        )

        rotate_secret_lambda = aws_lambda.Function(
            self,
            "rotate-secret-lambda-function",
            description="CMS Provisioning rotate secrets lambda function",
            handler="function.main.handler",
            function_name=rotate_secret_lambda_function_name,
            runtime=aws_lambda.Runtime.PYTHON_3_10,
            code=aws_lambda.Code.from_asset("dist/lambda/rotate_secret.zip"),
            timeout=Duration.seconds(60),
            role=rotate_secret_lambda_role,
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
            environment={
                "USER_AGENT_STRING": solution_config_inputs.get_user_agent_string(),
                "CLAIM_CERT_PROVISIONING_POLICY_NAME": claim_cert_provisioning_policy_name,
            },
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
        )

        # Add permission for Secrets Manager to invoke the rotate secrets lambda functions
        rotate_secret_lambda.add_permission(
            id="secrets-manager-invoke-rotate-secret-lambda-permission",
            principal=aws_iam.ServicePrincipal("secretsmanager.amazonaws.com"),
            action="lambda:InvokeFunction",
            source_account=Stack.of(self).account,
        )

        iot_credentials_custom_resource_policy = aws_iam.Policy(
            self,
            "custom-resource-policy",
            statements=[
                aws_iam.PolicyStatement(
                    actions=[
                        "iot:CreateKeysAndCertificate",
                    ],
                    effect=aws_iam.Effect.ALLOW,
                    resources=["*"],
                ),
                aws_iam.PolicyStatement(
                    actions=[
                        "secretsmanager:GetSecretValue",
                        "secretsmanager:DescribeSecret",
                        "secretsmanager:RotateSecret",
                    ],
                    effect=aws_iam.Effect.ALLOW,
                    resources=[
                        Stack.of(self).format_arn(
                            service="secretsmanager",
                            resource="secret",
                            resource_name=f"{provisioning_secret_name}*",
                            arn_format=ArnFormat.COLON_RESOURCE_NAME,
                        ),
                    ],
                ),
                aws_iam.PolicyStatement(
                    actions=["lambda:InvokeFunction"],
                    effect=aws_iam.Effect.ALLOW,
                    resources=[
                        rotate_secret_lambda.function_arn,
                    ],
                ),
                aws_iam.PolicyStatement(
                    actions=[
                        "secretsmanager:CreateSecret",
                    ],
                    effect=aws_iam.Effect.ALLOW,
                    resources=[
                        Stack.of(self).format_arn(
                            service="secretsmanager",
                            resource="secret",
                            resource_name="*",
                            arn_format=ArnFormat.COLON_RESOURCE_NAME,
                        ),
                    ],
                ),
                aws_iam.PolicyStatement(
                    actions=["iot:DeleteCertificate"],
                    effect=aws_iam.Effect.ALLOW,
                    resources=[
                        Stack.of(self).format_arn(
                            service="iot",
                            resource="cert",
                            resource_name="*",
                            arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                        ),
                    ],
                ),
            ],
        )
        custom_resource_lambda_construct.add_policy_to_custom_resource_lambda(
            policy=iot_credentials_custom_resource_policy,
        )

        self.credentials = CustomResource(
            self,
            "load-or-create-iot-credentials",
            service_token=custom_resource_lambda_construct.function.function_arn,
            resource_type=f"Custom::{CustomResourceFunctionType.LOAD_OR_CREATE_IOT_CREDENTIALS.value}",
            properties={
                "Resource": CustomResourceFunctionType.LOAD_OR_CREATE_IOT_CREDENTIALS.value,
                "IoTCredentialsSecretId": provisioning_secret_name,
                "RotateSecretLambdaARN": rotate_secret_lambda.function_arn,
            },
        )
        self.credentials.node.add_dependency(iot_credentials_custom_resource_policy)
