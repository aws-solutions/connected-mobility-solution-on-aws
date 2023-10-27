# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any

# Third Party Libraries
from aws_cdk import (
    ArnFormat,
    Duration,
    NestedStack,
    Stack,
    aws_iam,
    aws_lambda,
    aws_logs,
    aws_ssm,
)
from constructs import Construct

# Connected Mobility Solution on AWS
from ...config.constants import VPConstants
from ..lib.policy_generators import generate_lambda_cloudwatch_logs_policy_document


class AuxiliaryLambdasStack(NestedStack):
    def __init__(
        self,
        scope: Construct,
        stack_id: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, stack_id, **kwargs)

        self.rotate_secret_lambda = self.setup_rotate_secret_lambda_function()
        self.custom_resource_lambda = self.setup_custom_resource_lambda_function()

    def setup_custom_resource_lambda_function(self) -> aws_lambda.Function:
        custom_resource_lambda_function_name = (
            f"{VPConstants.APP_NAME}-custom-resource-lambda"
        )
        custom_resource_lambda_role = aws_iam.Role(
            self,
            "custom-resource-lambda-role",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            path="/",
            inline_policies={
                "lambda-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            actions=["lambda:InvokeFunction"],
                            effect=aws_iam.Effect.ALLOW,
                            resources=[
                                Stack.of(self).format_arn(
                                    service="lambda",
                                    resource="function",
                                    resource_name=self.rotate_secret_lambda.function_name,
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
                                "iot:CreateKeysAndCertificate",
                                "iot:UpdateEventConfigurations",
                            ],
                            effect=aws_iam.Effect.ALLOW,
                            resources=["*"],
                        ),
                        aws_iam.PolicyStatement(
                            actions=["iot:DeleteCertificate", "iot:UpdateCertificate"],
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
                                "iot:ListTargetsForPolicy",
                                "iot:DetachPolicy",
                            ],
                            effect=aws_iam.Effect.ALLOW,
                            resources=[
                                Stack.of(self).format_arn(
                                    service="iot",
                                    resource="policy",
                                    resource_name=VPConstants.CLAIM_CERT_PROVISIONING_POLICY_NAME,
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                                Stack.of(self).format_arn(
                                    service="iot",
                                    resource="cert",
                                    resource_name="*",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                            ],
                        ),
                    ]
                ),
                "secrets-manager-policy": aws_iam.PolicyDocument(
                    statements=[
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
                                    resource_name=f"{VPConstants.STAGE}/{VPConstants.APP_NAME}/provisioning-credentials*",
                                    arn_format=ArnFormat.COLON_RESOURCE_NAME,
                                ),
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
                    ]
                ),
                "cloudwatch-policy": generate_lambda_cloudwatch_logs_policy_document(
                    self,
                    lambda_function_name=custom_resource_lambda_function_name,
                ),
            },
        )

        custom_resource_lambda = aws_lambda.Function(
            self,
            "custom-resource-lambda",
            description="CMS provisioning custom resource lambda function",
            handler="custom_resource.custom_resource.handler",
            function_name=custom_resource_lambda_function_name,
            runtime=aws_lambda.Runtime.PYTHON_3_10,
            code=aws_lambda.Code.from_asset("source/handlers"),
            timeout=Duration.seconds(60),
            role=custom_resource_lambda_role,
            layers=[
                aws_lambda.LayerVersion.from_layer_version_arn(
                    self,
                    "custom-resource-lambda-dependency-layer-version",
                    aws_ssm.StringParameter.from_string_parameter_name(
                        self,
                        "custom-resource-lambda-dependency-layer-arn",
                        f"/{VPConstants.STAGE}/{VPConstants.APP_NAME}/arns/dependency-layer-arn",
                    ).string_value,
                )
            ],
            environment={
                "USER_AGENT_STRING": VPConstants.USER_AGENT_STRING,
            },
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
        )

        aws_ssm.StringParameter(
            self,
            "custom-resource-lambda-arn",
            string_value=custom_resource_lambda.function_arn,
            description="Arn for lambda function that services custom resources",
            parameter_name=f"/{VPConstants.STAGE}/{VPConstants.APP_NAME}/arns/custom-resource-lambda-arn",
        )

        return custom_resource_lambda

    def setup_rotate_secret_lambda_function(self) -> aws_lambda.Function:
        rotate_secret_lambda_function_name = (
            f"{VPConstants.APP_NAME}-rotate-secret-lambda"
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
                                    resource_name=f"{VPConstants.STAGE}/{VPConstants.APP_NAME}/provisioning-credentials*",
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
                                    resource_name=VPConstants.CLAIM_CERT_PROVISIONING_POLICY_NAME,
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
            },
        )

        rotate_secret_lambda = aws_lambda.Function(
            self,
            "rotate-secret-lambda",
            description="CMS provisioning rotate secrets lambda function",
            handler="rotate_secret.rotate_secret.handler",
            function_name=rotate_secret_lambda_function_name,
            runtime=aws_lambda.Runtime.PYTHON_3_10,
            code=aws_lambda.Code.from_asset("source/handlers"),
            timeout=Duration.seconds(60),
            role=rotate_secret_lambda_role,
            layers=[
                aws_lambda.LayerVersion.from_layer_version_arn(
                    self,
                    "rotate-secret-lambda-dependency-layer-version",
                    aws_ssm.StringParameter.from_string_parameter_name(
                        self,
                        "rotate-secret-lambda-dependency-layer-arn",
                        f"/{VPConstants.STAGE}/{VPConstants.APP_NAME}/arns/dependency-layer-arn",
                    ).string_value,
                )
            ],
            environment={
                "USER_AGENT_STRING": VPConstants.USER_AGENT_STRING,
                "CLAIM_CERT_PROVISIONING_POLICY_NAME": VPConstants.CLAIM_CERT_PROVISIONING_POLICY_NAME,
            },
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
        )

        # Add permission for Secrets Manager to invoke the rotate secrets lambda functions
        rotate_secret_lambda.add_permission(
            id="secrets-manager-invoke-rotate-secret-lambda-permission",
            principal=aws_iam.ServicePrincipal("secretsmanager.amazonaws.com"),
            action="lambda:InvokeFunction",
            source_account=str(self.account),
        )

        aws_ssm.StringParameter(
            self,
            "rotate-secret-lambda-arn",
            string_value=rotate_secret_lambda.function_arn,
            description="Arn for lambda function that rotates secrets",
            parameter_name=f"/{VPConstants.STAGE}/{VPConstants.APP_NAME}/arns/rotate-secret-lambda-arn",
        )

        return rotate_secret_lambda
