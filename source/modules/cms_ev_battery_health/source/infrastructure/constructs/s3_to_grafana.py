# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library

# AWS Libraries
from aws_cdk import (
    Duration,
    aws_ec2,
    aws_iam,
    aws_lambda,
    aws_lambda_event_sources,
    aws_logs,
    aws_s3,
)
from constructs import Construct

# CMS Common Library
from cms_common.config.resource_names import ResourceName, ResourcePrefix
from cms_common.config.stack_inputs import SolutionConfigInputs
from cms_common.constructs.encrypted_s3 import EncryptedS3Construct
from cms_common.constructs.vpc_construct import VpcConstruct
from cms_common.policy_generators.cloudwatch import (
    generate_lambda_cloudwatch_logs_policy_document,
)
from cms_common.policy_generators.ec2_vpc import generate_ec2_vpc_policy

# Connected Mobility Solution on AWS
from .module_integration import ModuleInputsConstruct


class S3ToGrafanaConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        solution_config_inputs: SolutionConfigInputs,
        module_inputs: ModuleInputsConstruct,
        dependency_layer: aws_lambda.LayerVersion,
        grafana_api_key_secret_arn: str,
        grafana_workspace_endpoint: str,
        dashboard_s3_object_key_prefix: str,
        alerts_s3_object_key_prefix: str,
        vpc_construct: VpcConstruct,
    ) -> None:
        super().__init__(scope, construct_id)

        self.grafana_assets_bucket = EncryptedS3Construct(
            self,
            "grafana-assets",
            retain_on_stack_delete=False,
            log_lifecycle_rules=module_inputs.s3_log_lifecycle_rules,
        )

        s3_to_grafana_lambda_function_name = ResourceName.hyphen_separated(
            prefix=ResourcePrefix.hyphen_separated(
                app_unique_id=module_inputs.app_unique_id,
                module_name=solution_config_inputs.module_short_name,
            ),
            name="s3-to-grafana",
        )

        s3_to_grafana_lambda_role = aws_iam.Role(
            self,
            "lambda-role",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            inline_policies={
                "secretsmanager-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            actions=[
                                "secretsmanager:GetSecretValue",
                            ],
                            effect=aws_iam.Effect.ALLOW,
                            resources=[
                                grafana_api_key_secret_arn,
                            ],
                        ),
                    ]
                ),
                "s3-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            actions=[
                                "s3:GetObject",
                            ],
                            effect=aws_iam.Effect.ALLOW,
                            resources=[
                                f"{self.grafana_assets_bucket.bucket.bucket_arn}/{dashboard_s3_object_key_prefix}*",
                                f"{self.grafana_assets_bucket.bucket.bucket_arn}/{alerts_s3_object_key_prefix}*",
                            ],
                        ),
                    ]
                ),
                "cloudwatch-policy": generate_lambda_cloudwatch_logs_policy_document(
                    self,
                    lambda_function_name=s3_to_grafana_lambda_function_name,
                ),
                "ec2-vpc-policy": generate_ec2_vpc_policy(
                    self,
                    vpc_construct=vpc_construct,
                    subnet_selection=vpc_construct.private_subnet_selection,
                    authorized_service="lambda.amazonaws.com",
                ),
            },
        )

        s3_to_grafana_lambda = aws_lambda.Function(
            self,
            "lambda-function",
            description="CMS EV battery health update s3 assets to grafana lambda function",
            handler="function.main.handler",
            function_name=s3_to_grafana_lambda_function_name,
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            code=aws_lambda.Code.from_asset("deployment/dist/lambda/s3_to_grafana.zip"),
            timeout=Duration.seconds(60),
            role=s3_to_grafana_lambda_role,
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
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
                "GRAFANA_API_KEY_SECRET_ARN": grafana_api_key_secret_arn,
                "GRAFANA_WORKSPACE_ENDPOINT": grafana_workspace_endpoint,
                "DASHBOARD_S3_OBJECT_KEY_PREFIX": dashboard_s3_object_key_prefix,
                "ALERTS_S3_OBJECT_KEY_PREFIX": alerts_s3_object_key_prefix,
            },
        )

        # call the s3 to grafana lambda whenever an object with desired prefix
        # is uploaded to the s3 bucket
        dashboard_s3_event_source = aws_lambda_event_sources.S3EventSource(
            bucket=self.grafana_assets_bucket.bucket,
            events=[aws_s3.EventType.OBJECT_CREATED],
            filters=[
                aws_s3.NotificationKeyFilter(
                    prefix=dashboard_s3_object_key_prefix,
                ),
            ],
        )
        alerts_s3_event_source = aws_lambda_event_sources.S3EventSource(
            bucket=self.grafana_assets_bucket.bucket,
            events=[aws_s3.EventType.OBJECT_CREATED],
            filters=[
                aws_s3.NotificationKeyFilter(
                    prefix=alerts_s3_object_key_prefix,
                ),
            ],
        )

        s3_to_grafana_lambda.add_event_source(dashboard_s3_event_source)
        s3_to_grafana_lambda.add_event_source(alerts_s3_event_source)
