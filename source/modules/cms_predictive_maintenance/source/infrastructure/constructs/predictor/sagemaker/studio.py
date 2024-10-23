# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# AWS Libraries
from aws_cdk import ArnFormat, CustomResource, Stack, aws_iam, aws_kms, aws_sagemaker
from constructs import Construct

# CMS Common Library
from cms_common.config.resource_names import ResourceName, ResourcePrefix
from cms_common.config.stack_inputs import SolutionConfigInputs
from cms_common.constructs.custom_resource_lambda import CustomResourceLambdaConstruct
from cms_common.constructs.vpc_construct import VpcConstruct

# Connected Mobility Solution on AWS
from .....handlers.custom_resource.function.lib.custom_resource_type_enum import (
    CustomResourceFunctionType,
)


class SageMakerStudioConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_unique_id: str,
        vpc_construct: VpcConstruct,
        solution_config_inputs: SolutionConfigInputs,
        custom_resource_lambda_construct: CustomResourceLambdaConstruct,
    ) -> None:
        super().__init__(scope, construct_id)

        role = aws_iam.Role(
            self,
            "role",
            assumed_by=aws_iam.ServicePrincipal("sagemaker.amazonaws.com"),
            description="SageMaker Domain Role",
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
                "cloudwatch": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "logs:CreateLogGroup",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents",
                                "logs:DescribeLogStreams",
                                "logs:GetLogEvents",
                            ],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="logs",
                                    resource="log-group",
                                    resource_name="/aws/sagemaker/*",
                                    arn_format=ArnFormat.COLON_RESOURCE_NAME,
                                ),
                                Stack.of(self).format_arn(
                                    service="logs",
                                    resource="log-group",
                                    resource_name="/aws/sagemaker/*:log-stream:*",
                                    arn_format=ArnFormat.COLON_RESOURCE_NAME,
                                ),
                            ],
                        ),
                    ]
                ),
            },
        )

        kms_key = aws_kms.Key(
            self,
            "cmk-key",
            enable_key_rotation=True,
        )

        sagemaker_studio_name = ResourceName.hyphen_separated(
            prefix=ResourcePrefix.hyphen_separated(
                app_unique_id=app_unique_id,
                module_name=solution_config_inputs.module_short_name,
            ),
            name="studio",
        )

        sagemaker_domain = aws_sagemaker.CfnDomain(
            self,
            "sagemaker-domain",
            auth_mode="IAM",
            default_user_settings=aws_sagemaker.CfnDomain.UserSettingsProperty(
                execution_role=role.role_arn,
            ),
            domain_name=sagemaker_studio_name,
            subnet_ids=vpc_construct.vpc.select_subnets(
                selection=vpc_construct.private_subnet_selection
            ).get("subnetIds"),
            vpc_id=vpc_construct.vpc.vpc_id,
            kms_key_id=kms_key.key_id,
        )

        custom_resource_policy = aws_iam.Policy(
            self,
            "custom-resource-policy",
            statements=[
                aws_iam.PolicyStatement(
                    actions=[
                        "elasticfilesystem:DeleteFileSystem",
                        "elasticfilesystem:DescribeMountTargets",
                        "elasticfilesystem:DescribeMountTargetSecurityGroups",
                        "elasticfilesystem:DeleteMountTarget",
                    ],
                    effect=aws_iam.Effect.ALLOW,
                    resources=[
                        Stack.of(self).format_arn(
                            service="elasticfilesystem",
                            resource="file-system",
                            resource_name=sagemaker_domain.attr_home_efs_file_system_id,
                            arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                        ),
                    ],
                ),
                aws_iam.PolicyStatement(
                    actions=[
                        "ec2:DeleteSecurityGroup",
                        "ec2:DescribeSecurityGroups",
                        "ec2:RevokeSecurityGroupEgress",
                        "ec2:RevokeSecurityGroupIngress",
                    ],
                    effect=aws_iam.Effect.ALLOW,
                    resources=["*"],
                ),
            ],
        )
        custom_resource_lambda_construct.add_policy_to_custom_resource_lambda(
            policy=custom_resource_policy,
        )

        delete_sagemaker_domain_efs_custom_resource = CustomResource(
            self,
            "delete-sagemaker-domain-efs-custom-resource",
            service_token=custom_resource_lambda_construct.function.function_arn,
            resource_type=f"Custom::{CustomResourceFunctionType.DELETE_SAGEMAKER_DOMAIN_EFS.value}",
            properties={
                "Resource": CustomResourceFunctionType.DELETE_SAGEMAKER_DOMAIN_EFS.value,
                "HomeEfsFileSystemId": sagemaker_domain.attr_home_efs_file_system_id,
            },
        )
        delete_sagemaker_domain_efs_custom_resource.node.add_dependency(
            custom_resource_policy
        )

        sagemaker_admin_user_name = ResourceName.hyphen_separated(
            prefix=ResourcePrefix.hyphen_separated(
                app_unique_id=app_unique_id,
                module_name=solution_config_inputs.module_short_name,
            ),
            name="admin",
        )

        aws_sagemaker.CfnUserProfile(
            self,
            "sagemaker-admin-user-profile",
            domain_id=sagemaker_domain.attr_domain_id,
            user_profile_name=sagemaker_admin_user_name,
        )
