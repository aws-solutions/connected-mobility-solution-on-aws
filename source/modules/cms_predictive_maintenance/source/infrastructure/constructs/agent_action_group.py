# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json

# AWS Libraries
from aws_cdk import (
    ArnFormat,
    Duration,
    Stack,
    aws_bedrock,
    aws_ec2,
    aws_iam,
    aws_lambda,
    aws_logs,
)
from constructs import Construct

# CMS Common Library
from cms_common.config.resource_names import ResourceName, ResourcePrefix
from cms_common.config.stack_inputs import SolutionConfigInputs
from cms_common.constructs.cmk_encrypted_s3 import CMKEncryptedS3Construct
from cms_common.constructs.vpc_construct import VpcConstruct
from cms_common.policy_generators.cloudwatch import (
    generate_lambda_cloudwatch_logs_policy_document,
)
from cms_common.policy_generators.ec2_vpc import generate_ec2_vpc_policy
from cms_common.policy_generators.kms import generate_kms_policy_statement_from_key_id


class AgentActionGroupConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_unique_id: str,
        solution_config_inputs: SolutionConfigInputs,
        dependency_layer: aws_lambda.LayerVersion,
        vpc_construct: VpcConstruct,
        sagemaker_assets_bucket_construct: CMKEncryptedS3Construct,
        inference_data_s3_key_prefix: str,
    ) -> None:
        super().__init__(scope, construct_id)

        agent_action_group_lambda_name = ResourceName.hyphen_separated(
            prefix=ResourcePrefix.hyphen_separated(
                app_unique_id=app_unique_id,
                module_name=solution_config_inputs.module_short_name,
            ),
            name="action-group",
        )

        self.role = aws_iam.Role(
            self,
            "lambda-role",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            inline_policies={
                "lambda-logs-policy": generate_lambda_cloudwatch_logs_policy_document(
                    self, agent_action_group_lambda_name
                ),
                "ec2-policy": generate_ec2_vpc_policy(
                    self,
                    vpc_construct=vpc_construct,
                    subnet_selection=vpc_construct.private_subnet_selection,
                    authorized_service="lambda.amazonaws.com",
                ),
                "prediction-results-s3-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "s3:ListBucket",
                            ],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="s3",
                                    resource=sagemaker_assets_bucket_construct.bucket.bucket_name,
                                    resource_name=None,
                                    account="",
                                    region="",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                            ],
                        ),
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "s3:GetObject",
                            ],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="s3",
                                    resource=sagemaker_assets_bucket_construct.bucket.bucket_name,
                                    resource_name=f"{inference_data_s3_key_prefix}/*",
                                    account="",
                                    region="",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                            ],
                        ),
                        generate_kms_policy_statement_from_key_id(
                            self,
                            kms_encryption_key_id=sagemaker_assets_bucket_construct.key.key_id,
                            allow_encrypt=False,
                        ),
                    ]
                ),
            },
        )

        security_group = aws_ec2.SecurityGroup(
            self,
            "security-group",
            vpc=vpc_construct.vpc,
            allow_all_outbound=True,  # NOSONAR
        )

        self.function = aws_lambda.Function(
            self,
            "lambda-function",
            code=aws_lambda.Code.from_asset(
                "dist/lambda/agent_action_group.zip",
                exclude=["**/tests/*"],
            ),
            handler="function.main.handler",
            function_name=agent_action_group_lambda_name,
            role=self.role,
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            timeout=Duration.minutes(1),
            layers=[dependency_layer],
            memory_size=512,
            environment={
                "USER_AGENT_STRING": solution_config_inputs.get_user_agent_string(),
                "INFERENCE_DATA_S3_BUCKET_NAME": sagemaker_assets_bucket_construct.bucket.bucket_name,
                "INFERENCE_INPUT_DATA_S3_KEY": f"{inference_data_s3_key_prefix}/latest.csv",
                "INFERENCE_OUTPUT_DATA_S3_KEY": f"{inference_data_s3_key_prefix}/latest.csv.out",
            },
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
            vpc=vpc_construct.vpc,
            vpc_subnets=vpc_construct.private_subnet_selection,
            security_groups=[security_group],
        )

        self.function.grant_invoke(aws_iam.ServicePrincipal("bedrock.amazonaws.com"))

        with open(
            "source/handlers/agent_action_group/function/openapi.json",
            "r",
            encoding="utf-8",
        ) as f:
            api_schema = json.load(f)

        self.action_group = aws_bedrock.CfnAgent.AgentActionGroupProperty(
            action_group_name="vehicle-maintenance-status",
            action_group_executor=aws_bedrock.CfnAgent.ActionGroupExecutorProperty(
                lambda_=self.function.function_arn,
            ),
            action_group_state="ENABLED",
            api_schema=aws_bedrock.CfnAgent.APISchemaProperty(
                payload=json.dumps(api_schema),
            ),
        )
