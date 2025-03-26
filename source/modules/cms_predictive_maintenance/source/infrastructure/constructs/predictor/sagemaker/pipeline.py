# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from dataclasses import dataclass

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
    aws_sagemaker,
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
from .....handlers.custom_resource.function.lib.custom_resource_type_enum import (
    CustomResourceFunctionType,
)


@dataclass(frozen=True)
class PipelineAssetsS3Config:
    bucket_name: str
    pipeline_definition_object_key: str


class SageMakerPipelineConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_unique_id: str,
        solution_config_inputs: SolutionConfigInputs,
        custom_resource_lambda_construct: CustomResourceLambdaConstruct,
        pipeline_assets_s3_config: PipelineAssetsS3Config,
        vpc_construct: VpcConstruct,
        dependency_layer: aws_lambda.LayerVersion,
    ) -> None:
        super().__init__(scope, construct_id)

        pipeline_role_name = (
            ResourceName.hyphen_separated(
                prefix=ResourcePrefix.hyphen_separated(
                    app_unique_id=app_unique_id,
                    module_name=solution_config_inputs.module_short_name,
                ),
                name="pipeline-role",
            )
            + "-"
            + Stack.of(self).region
        )

        self.deploy_model_endpoint_name = ResourceName.hyphen_separated(
            prefix=ResourcePrefix.hyphen_separated(
                app_unique_id=app_unique_id,
                module_name=solution_config_inputs.module_short_name,
            ),
            name="endpoint",
        )

        deploy_pipeline_model_lambda_function_name = ResourceName.hyphen_separated(
            prefix=ResourcePrefix.hyphen_separated(
                app_unique_id=app_unique_id,
                module_name=solution_config_inputs.module_short_name,
            ),
            name="deploy-pipeline-model",
        )

        deploy_pipeline_model_role = aws_iam.Role(
            self,
            "deploy-pipeline-model-lambda-role",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            inline_policies={
                "lambda-logs-policy": generate_lambda_cloudwatch_logs_policy_document(
                    self, deploy_pipeline_model_lambda_function_name
                ),
                "ec2-policy": generate_ec2_vpc_policy(
                    self,
                    vpc_construct=vpc_construct,
                    subnet_selection=vpc_construct.private_subnet_selection,
                    authorized_service="lambda.amazonaws.com",
                ),
                "sagemaker": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            actions=[
                                "sagemaker:ListModelPackages",
                                "sagemaker:CreateModel",
                                "sagemaker:CreateEndpointConfig",
                                "sagemaker:CreateEndpoint",
                                "sagemaker:UpdateEndpoint",
                            ],
                            resources=["*"],  # NOSONAR
                        ),
                    ],
                ),
                "iam": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            actions=[
                                "iam:PassRole",
                            ],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="iam",
                                    resource="role",
                                    resource_name=pipeline_role_name,
                                    region="",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                            ],
                            conditions={
                                "StringEquals": {
                                    "iam:PassedToService": "sagemaker.amazonaws.com"
                                }
                            },
                        )
                    ],
                ),
            },
        )

        security_group = aws_ec2.SecurityGroup(
            self,
            "security-group",
            vpc=vpc_construct.vpc,
            allow_all_outbound=True,  # NOSONAR
        )

        self.deploy_pipeline_model_function = aws_lambda.Function(
            self,
            "deploy-pipeline-model-lambda-function",
            code=aws_lambda.Code.from_asset(
                "deployment/dist/lambda/deploy_pipeline_model.zip",
                exclude=["**/tests/*"],
            ),
            handler="function.main.handler",
            function_name=deploy_pipeline_model_lambda_function_name,
            role=deploy_pipeline_model_role,
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            timeout=Duration.minutes(1),
            layers=[dependency_layer],
            memory_size=512,
            environment={
                "USER_AGENT_STRING": solution_config_inputs.get_user_agent_string(),
            },
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
            vpc=vpc_construct.vpc,
            vpc_subnets=vpc_construct.private_subnet_selection,
            security_groups=[security_group],
        )

        self.deploy_pipeline_model_function.grant_invoke(
            aws_iam.ServicePrincipal("sagemaker.amazonaws.com")
        )

        self.role = aws_iam.Role(
            self,
            "role",
            role_name=pipeline_role_name,
            assumed_by=aws_iam.ServicePrincipal("sagemaker.amazonaws.com"),
            inline_policies={
                "sagemaker": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            actions=[
                                "sagemaker:*",
                            ],
                            resources=["*"],  # NOSONAR
                        ),
                    ],
                ),
                "s3": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            actions=[
                                "s3:ListBucket",
                                "s3:GetObject",
                                "s3:PutObject",
                            ],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="s3",
                                    resource=pipeline_assets_s3_config.bucket_name,
                                    resource_name=None,
                                    account="",
                                    region="",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                                Stack.of(self).format_arn(
                                    service="s3",
                                    resource=pipeline_assets_s3_config.bucket_name,
                                    resource_name="*",
                                    account="",
                                    region="",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                            ],
                        ),
                    ],
                ),
                "iam": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            actions=[
                                "iam:PassRole",
                            ],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="iam",
                                    resource="role",
                                    resource_name=pipeline_role_name,
                                    region="",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                            ],
                            conditions={
                                "StringEquals": {
                                    "iam:PassedToService": "sagemaker.amazonaws.com"
                                }
                            },
                        )
                    ],
                ),
                "cloudwatch": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            actions=[
                                "logs:CreateLogDelivery",
                                "logs:CreateLogGroup",
                                "logs:CreateLogStream",
                                "logs:DeleteLogDelivery",
                                "logs:Describe*",
                                "logs:GetLogDelivery",
                                "logs:GetLogEvents",
                                "logs:ListLogDeliveries",
                                "logs:PutLogEvents",
                                "logs:PutResourcePolicy",
                                "logs:UpdateLogDelivery",
                            ],
                            resources=["*"],
                        )
                    ],
                ),
                "lambda": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            actions=[
                                "lambda:InvokeFunction",
                            ],
                            resources=[
                                self.deploy_pipeline_model_function.function_arn
                            ],
                        )
                    ],
                ),
                "ecr": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            actions=[
                                "ecr:BatchCheckLayerAvailability",
                                "ecr:BatchGetImage",
                                "ecr:DescribeImages",
                                "ecr:GetAuthorizationToken",
                                "ecr:GetDownloadUrlForLayer",
                            ],
                            resources=["*"],
                        )
                    ],
                ),
            },
        )

        sagemaker_pipeline_name = ResourceName.hyphen_separated(
            prefix=ResourcePrefix.hyphen_separated(
                app_unique_id=app_unique_id,
                module_name=solution_config_inputs.module_short_name,
            ),
            name="pipeline",
        )

        custom_resource_policy = aws_iam.Policy(
            self,
            "custom-resource-policy",
            statements=[
                aws_iam.PolicyStatement(
                    actions=[
                        "s3:PutObject",
                    ],
                    effect=aws_iam.Effect.ALLOW,
                    resources=[
                        Stack.of(self).format_arn(
                            service="s3",
                            resource=pipeline_assets_s3_config.bucket_name,
                            resource_name=pipeline_assets_s3_config.pipeline_definition_object_key,
                            account="",
                            region="",
                            arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                        ),
                    ],
                ),
                aws_iam.PolicyStatement(
                    actions=[
                        "s3:ListBucket",
                        "s3:PutObject",
                    ],
                    resources=[
                        Stack.of(self).format_arn(
                            service="s3",
                            resource=pipeline_assets_s3_config.bucket_name,
                            resource_name=None,
                            account="",
                            region="",
                            arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                        ),
                        Stack.of(self).format_arn(
                            service="s3",
                            resource=pipeline_assets_s3_config.bucket_name,
                            resource_name="*",
                            account="",
                            region="",
                            arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                        ),
                    ],
                ),
            ],
        )
        custom_resource_lambda_construct.add_policy_to_custom_resource_lambda(
            policy=custom_resource_policy,
        )

        create_and_upload_sagemaker_pipeline_definition = CustomResource(
            self,
            "create-and-upload-sagemaker-pipeline-definition-custom-resource",
            service_token=custom_resource_lambda_construct.function.function_arn,
            resource_type=f"Custom::{CustomResourceFunctionType.CREATE_AND_UPLOAD_SAGEMAKER_PIPELINE_DEFINITION.value}",
            properties={
                "Resource": CustomResourceFunctionType.CREATE_AND_UPLOAD_SAGEMAKER_PIPELINE_DEFINITION.value,
                "PipelineName": sagemaker_pipeline_name,
                "PipelineAssetsBucketName": pipeline_assets_s3_config.bucket_name,
                "PipelineDefinitionS3Key": pipeline_assets_s3_config.pipeline_definition_object_key,
                "PipelineRoleArn": self.role.role_arn,
                "PipelineDeployModelLambdaArn": self.deploy_pipeline_model_function.function_arn,
                "SageMakerModelEndpointName": self.deploy_model_endpoint_name,
                "ResourceNameSuffix": ResourcePrefix.hyphen_separated(
                    app_unique_id=app_unique_id,
                    module_name=solution_config_inputs.module_short_name,
                ),
            },
        )

        pipeline = aws_sagemaker.CfnPipeline(
            self,
            "pipeline",
            pipeline_name=sagemaker_pipeline_name,
            pipeline_definition={
                "PipelineDefinitionS3Location": {
                    "Bucket": pipeline_assets_s3_config.bucket_name,
                    "Key": pipeline_assets_s3_config.pipeline_definition_object_key,
                },
            },
            role_arn=self.role.role_arn,
        )
        pipeline.node.add_dependency(create_and_upload_sagemaker_pipeline_definition)
