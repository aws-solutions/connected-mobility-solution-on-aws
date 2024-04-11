# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any

# AWS Libraries
from aws_cdk import (
    ArnFormat,
    CfnMapping,
    Stack,
    aws_codebuild,
    aws_ec2,
    aws_iam,
    aws_kms,
)
from constructs import Construct

# Connected Mobility Solution on AWS
from .module_integration import ModuleInputsConstruct


class ModuleDeployCodeBuildConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        stack_id: str,
        solution_mapping: CfnMapping,
        cloudformation_role_arn: str,
        vpc: aws_ec2.IVpc,
        private_subnet_selection: aws_ec2.SubnetSelection,
        module_inputs: ModuleInputsConstruct,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, stack_id, **kwargs)

        code_build_iam_role = aws_iam.Role(
            self,
            "module-deploy-code-build-role",
            description="Module Deploy CodeBuild Role",
            assumed_by=aws_iam.ServicePrincipal("codebuild.amazonaws.com"),
            inline_policies={
                "s3-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "s3:GetBucketLocation",
                                "s3:GetObject",
                                "s3:ListBucket",
                            ],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="s3",
                                    resource=f'{solution_mapping.find_in_map("AssetsConfig", "S3AssetBucketBaseName")}-{Stack.of(self).region}',
                                    resource_name=None,
                                    account="",
                                    region="",
                                    arn_format=ArnFormat.NO_RESOURCE_NAME,
                                ),
                                Stack.of(self).format_arn(
                                    service="s3",
                                    resource=f'{solution_mapping.find_in_map("AssetsConfig", "S3AssetBucketBaseName")}-{Stack.of(self).region}',
                                    resource_name="*",
                                    account="",
                                    region="",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                                Stack.of(self).format_arn(
                                    service="s3",
                                    resource=module_inputs.local_asset_bucket_inputs.bucket_name,
                                    resource_name=None,
                                    account="",
                                    region="",
                                    arn_format=ArnFormat.NO_RESOURCE_NAME,
                                ),
                                Stack.of(self).format_arn(
                                    service="s3",
                                    resource=module_inputs.local_asset_bucket_inputs.bucket_name,
                                    resource_name="*",
                                    account="",
                                    region="",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                            ],
                        ),
                    ]
                ),
                "s3-kms-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "kms:GenerateDataKey",
                                "kms:Decrypt",
                                "kms:Encrypt",
                            ],
                            resources=[
                                module_inputs.local_asset_bucket_inputs.bucket_key_arn
                            ],
                        ),
                    ]
                ),
                "cloudformation-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "cloudformation:DescribeStacks",
                                "cloudformation:CreateChangeSet",
                                "cloudformation:DescribeChangeSet",
                                "cloudformation:ExecuteChangeSet",
                                "cloudformation:DeleteChangeSet",
                                "cloudformation:CreateStack",
                                "cloudformation:DeleteStack",
                                "cloudformation:GetTemplateSummary",
                            ],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="cloudformation",
                                    resource="stack",
                                    resource_name="*",  # stack names are user defined
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                            ],
                        ),
                    ]
                ),
                "iam-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=["iam:PassRole"],
                            resources=[cloudformation_role_arn],
                        )
                    ]
                ),
            },
        )

        module_deploy_security_group = aws_ec2.SecurityGroup(
            self,
            "module-deploy-project-security-group",
            allow_all_outbound=True,  # NOSONAR
            vpc=vpc,
        )

        self.codebuild_project = aws_codebuild.Project(
            self,
            "module-deploy-codebuild-project",
            project_name=f"{module_inputs.acdp_uid}-deployment-project",
            check_secrets_in_plain_text_env_variables=True,
            encryption_key=aws_kms.Key(
                self, "module-deploy-codebuild-key", enable_key_rotation=True
            ),
            environment=aws_codebuild.BuildEnvironment(
                compute_type=aws_codebuild.ComputeType.LARGE,
                build_image=aws_codebuild.LinuxBuildImage.STANDARD_7_0,
                environment_variables={
                    "CLOUDFORMATION_ROLE_ARN": aws_codebuild.BuildEnvironmentVariable(
                        value=cloudformation_role_arn,
                        type=aws_codebuild.BuildEnvironmentVariableType.PLAINTEXT,
                    ),
                },
            ),
            role=code_build_iam_role,
            build_spec=aws_codebuild.BuildSpec.from_object(
                {
                    "version": "0.2",
                    "phases": {"build": {"commands": ['echo "Hello, CodeBuild!"']}},
                }
            ),
            vpc=vpc,
            subnet_selection=private_subnet_selection,
            security_groups=[module_deploy_security_group],
        )
