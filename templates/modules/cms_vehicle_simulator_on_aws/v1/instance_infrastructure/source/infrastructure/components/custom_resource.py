# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

# Standard Library
from typing import TYPE_CHECKING, Optional

# Third Party Libraries
from aws_cdk import (
    ArnFormat,
    Aws,
    CustomResource,
    Duration,
    Fn,
    RemovalPolicy,
    Stack,
    aws_iam,
    aws_kms,
    aws_lambda,
    aws_logs,
    aws_ssm,
)
from constructs import Construct

# Connected Mobility Solution on AWS
from ...config.constants import VSConstants
from ...infrastructure import generate_lambda_cloudwatch_logs_policy_document

if TYPE_CHECKING:
    # Connected Mobility Solution on AWS
    from ..cms_vehicle_simulator_on_aws_stack import InfrastructureResourceStack


class CustomResourcesConstruct(Construct):
    def __init__(
        self,
        scope: InfrastructureResourceStack,
        stack_id: str,
        solution_id: Optional[str],
        solution_version: Optional[str],
    ) -> None:
        super().__init__(scope, stack_id)

        helper_lambda_name = f"{VSConstants.APP_NAME}-custom-resources-lambda"

        helper_lambda_kms_key = aws_kms.Key(
            self,
            "vs-helper-lambda-log-group-kms-key",
            alias="vs-helper-lambda-log-group-kms-key",
            enable_key_rotation=True,
        )

        self.helper_lambda_log_group = aws_logs.LogGroup(
            self,
            "helper-lambda-log-group",
            removal_policy=RemovalPolicy.RETAIN,
            retention=aws_logs.RetentionDays.THREE_MONTHS,
            encryption_key=helper_lambda_kms_key,
        )

        helper_lambda_kms_key.add_to_resource_policy(
            statement=aws_iam.PolicyStatement(
                effect=aws_iam.Effect.ALLOW,
                principals=[
                    aws_iam.ServicePrincipal(f"logs.{scope.region}.amazonaws.com")
                ],
                actions=["kms:Encrypt", "kms:Decrypt", "kms:GenerateDataKey"],
                resources=["*"],
            )
        )

        self.helper_lambda_role = aws_iam.Role(
            self,
            "helper-lambda-role",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            path="/",
            inline_policies={
                "lambda-dynamo-role": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=["dynamodb:PutItem"],
                            resources=[
                                aws_ssm.StringParameter.from_string_parameter_name(
                                    self,
                                    "ssm-templates-table-arn",
                                    f"/{VSConstants.STAGE}/{VSConstants.APP_NAME}/dynamodb/templates-table-arn",
                                ).string_value
                            ],
                        )
                    ]
                ),
                "lambda-s3-role": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=["s3:PutObject", "s3:AbortMultipartUpload"],
                            resources=[
                                f"{Fn.import_value(f'{VSConstants.APP_NAME}-console-bucket-arn')}/*",
                                f"{Fn.import_value(f'{VSConstants.APP_NAME}-routes-bucket-arn')}/*",
                            ],
                        ),
                    ]
                ),
                "lambda-cognito-role": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=["cognito-idp:AdminCreateUser"],
                            resources=[
                                Fn.import_value(
                                    f"{VSConstants.APP_NAME}-user-pool-arn"
                                ),
                            ],
                        )
                    ]
                ),
                "lambda-iot-role": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "iot:DescribeEndpoint",
                                "iot:CreateThingGroup",
                                "iot:TagResource",
                                "iot:DetachPrincipalPolicy",
                            ],
                            resources=["*"],  # NOSONAR
                            # These actions require a wildcard resource
                        ),
                        aws_iam.PolicyStatement(
                            actions=["iot:ListTargetsForPolicy"],
                            effect=aws_iam.Effect.ALLOW,
                            resources=[
                                Stack.of(self).format_arn(
                                    service="iot",
                                    resource="policy",
                                    resource_name="*",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                )
                            ],
                        ),
                    ]
                ),
                "lambda-cloudwatch-logs-role": generate_lambda_cloudwatch_logs_policy_document(
                    self, helper_lambda_name
                ),
            },
        )

        self.helper_lambda = aws_lambda.Function(
            self,
            "helper-lambda",
            description="CMS Vehicle Simulator custom resource function",
            handler="custom_resource.custom_resource.handler",
            function_name=helper_lambda_name,
            runtime=aws_lambda.Runtime.PYTHON_3_10,
            code=aws_lambda.Code.from_asset("source/handlers"),
            timeout=Duration.seconds(60),
            role=self.helper_lambda_role,
            environment={
                "SOLUTION_ID": solution_id or "N/A",
                "SOLUTION_VERSION": solution_version or "N/A",
                "USER_AGENT_STRING": VSConstants.USER_AGENT_STRING,
            },
            layers=[
                aws_lambda.LayerVersion.from_layer_version_arn(
                    self,
                    "layer-version",
                    aws_ssm.StringParameter.from_string_parameter_name(
                        self,
                        "ssm-dependency-layer-arn",
                        f"/{VSConstants.STAGE}/{VSConstants.APP_NAME}/arns/dependency-layer-arn",
                    ).string_value,
                )
            ],
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
        )

        self.custom_ids = CustomResource(
            self,
            "console-uuid-custom-resource",
            service_token=self.helper_lambda.function_arn,
            properties={"Resource": "CreateUUID", "StackName": Aws.STACK_NAME},
        )

        CustomResource(
            self,
            "console-cognito-user",
            service_token=self.helper_lambda.function_arn,
            resource_type="Custom::CreateUserpoolUser",
            properties={
                "Resource": "CreateUserpoolUser",
                "UserpoolId": Fn.import_value(f"{VSConstants.APP_NAME}-user-pool-id"),
                "DesiredDeliveryMediums": ["EMAIL"],
                "ForceAliasCreation": "true",
                "Username": Fn.import_value(f"{VSConstants.APP_NAME}-admin-email"),
                "UserAttributes": [
                    {
                        "Name": "email",
                        "Value": Fn.import_value(f"{VSConstants.APP_NAME}-admin-email"),
                    },
                    {"Name": "email_verified", "Value": True},
                ],
            },
        )

        self.simulator_thing_group = CustomResource(
            self,
            "simulator-thing-group",
            service_token=self.helper_lambda.function_arn,
            resource_type="Custom::CreateIoTThingGroup",
            properties={
                "Resource": "CreateIoTThingGroup",
                "ThingGroupName": "cms-simulated-vehicle",
            },
        )

        scope.export_value(
            self.helper_lambda.function_arn,
            name=f"{VSConstants.APP_NAME}-helper-function-arn",
        )
        scope.export_value(
            self.helper_lambda_role.role_arn,
            name=f"{VSConstants.APP_NAME}-helper-function-role-arn",
        )
        scope.export_value(
            self.custom_ids.get_att("UUID").to_string(),
            name=f"{VSConstants.APP_NAME}-uuid",
        )
        scope.export_value(
            self.custom_ids.get_att("UNIQUE_SUFFIX").to_string(),
            name=f"{VSConstants.APP_NAME}-unique-suffix",
        )
        scope.export_value(
            self.custom_ids.get_att("REDUCED_STACK_NAME").to_string(),
            name=f"{VSConstants.APP_NAME}-reduced-stack-name",
        )

        scope.export_value(
            self.simulator_thing_group.get_att("THING_GROUP_NAME").to_string(),
            name=f"{VSConstants.APP_NAME}-thing-group-name",
        )
