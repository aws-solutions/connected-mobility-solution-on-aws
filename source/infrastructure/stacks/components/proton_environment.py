# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
import tarfile
from typing import Any

# Third Party Libraries
from aws_cdk import (
    ArnFormat,
    CustomResource,
    Stack,
    aws_iam,
    aws_kms,
    aws_s3,
    aws_s3_deployment,
)
from constructs import Construct

# Connected Mobility Solution on AWS
from ...constructs.custom_resource_lambda import CustomResourceLambdaConstruct


class ProtonEnvironment(Construct):
    def __init__(  # too-many-locals: ignore
        self,
        scope: Stack,
        stack_id: str,
        custom_resource_construct: CustomResourceLambdaConstruct,
        **kwargs: Any,
    ) -> None:  # too-many-locals: ignore
        super().__init__(scope, stack_id, **kwargs)

        s3_key = aws_kms.Key(
            self,
            "proton-environment-s3-key",
            enable_key_rotation=True,
        )

        proton_environment_s3_key_prefix = "cms_environment_templates"

        environment_bucket = aws_s3.Bucket(
            self,
            "proton-environment-bucket",
            block_public_access=aws_s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            server_access_logs_prefix="proton-environment-bucket/",
            encryption_key=s3_key,
            versioned=True,
            encryption=aws_s3.BucketEncryption.KMS,
        )

        code_build_iam_role = aws_iam.Role(
            self,
            "proton-code-build-role",
            assumed_by=aws_iam.ServicePrincipal("codebuild.amazonaws.com"),
            inline_policies={
                "s3-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "s3:GetObject",
                                "s3:GetBucketLocation",
                                "s3:ListBucket",
                            ],
                            resources=[
                                environment_bucket.bucket_arn,
                                f"arn:aws:s3:::cdk-*-assets-{Stack.of(self).account}-{Stack.of(self).region}",
                            ],
                        )
                    ]
                ),
                "cloudwatch-logs-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "logs:CreateLogGroup",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents",
                            ],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="logs",
                                    resource="log-group",
                                    resource_name="/aws/codebuild/AWSProton-*:log-stream:*",
                                    arn_format=ArnFormat.COLON_RESOURCE_NAME,
                                ),
                                Stack.of(self).format_arn(
                                    service="logs",
                                    resource="log-group",
                                    resource_name="/aws/codebuild/AWSProton-*",
                                    arn_format=ArnFormat.COLON_RESOURCE_NAME,
                                ),
                            ],
                        )
                    ]
                ),
                "cloudformation-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "cloudformation:DescribeStacks",
                                "cloudformation:CreateChangeSet",
                            ],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="cloudformation",
                                    resource="stack",
                                    resource_name="cms-environment/*",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                                Stack.of(self).format_arn(
                                    service="cloudformation",
                                    resource="stack",
                                    resource_name="CDKToolkit/*",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                            ],
                        ),
                    ]
                ),
                "ssm-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=["ssm:GetParameter"],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="ssm",
                                    resource="parameter",
                                    resource_name="cdk-bootstrap/*/*",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                            ],
                        )
                    ]
                ),
                "proton-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            actions=["proton:NotifyResourceDeploymentStatusChange"],
                            effect=aws_iam.Effect.ALLOW,
                            resources=[
                                Stack.of(self).format_arn(
                                    service="proton",
                                    resource="environment",
                                    resource_name="cms_environment",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                                Stack.of(self).format_arn(
                                    service="proton",
                                    resource="service",
                                    resource_name="*",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                            ],
                        )
                    ]
                ),
                "iam-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=["iam:PassRole"],
                            resources=[
                                f"arn:aws:iam::{Stack.of(self).account}:role/cdk-*-cfn-exec-role-{Stack.of(self).account}-{Stack.of(self).region}"
                            ],
                        )
                    ]
                ),
            },
        )

        code_build_iam_role.add_to_principal_policy(
            aws_iam.PolicyStatement(
                actions=["sts:AssumeRole"],
                effect=aws_iam.Effect.ALLOW,
                resources=[
                    code_build_iam_role.role_arn,
                    f"arn:aws:iam::{Stack.of(self).account}:role/cdk-*-file-publishing-role-{Stack.of(self).account}-{Stack.of(self).region}",
                    f"arn:aws:iam::{Stack.of(self).account}:role/cdk-*-deploy-role-{Stack.of(self).account}-{Stack.of(self).region}",
                ],
            )
        )

        environment_folder_path = os.path.abspath(
            os.path.join("templates", "environments")
        )

        def filter_environment_tar_folders(tarinfo: Any) -> Any:
            if ".venv" in tarinfo.name.split(os.path.sep):
                return None
            return tarinfo

        tar_folder_path = os.path.abspath(os.path.join("cdk.out", "environment_tars"))
        environments = os.listdir(environment_folder_path)
        if not os.path.exists(tar_folder_path):
            os.makedirs(tar_folder_path)
        for environment in environments:
            environment_path = os.path.join(environment_folder_path, environment)
            tar_file_path = os.path.join(tar_folder_path, environment) + ".tar.gz"
            if os.path.isdir(environment_path):
                with tarfile.open(tar_file_path, "w:gz") as tar:  # NOSONAR
                    tar.add(
                        environment_path,
                        arcname=os.path.basename(environment_path),
                        filter=filter_environment_tar_folders,
                    )

        s3_environment_templates = aws_s3_deployment.BucketDeployment(
            self,
            "proton-environment-templates-custom-deployment",
            sources=[aws_s3_deployment.Source.asset(tar_folder_path)],
            destination_bucket=environment_bucket,
            destination_key_prefix=proton_environment_s3_key_prefix,
            prune=True,
        )

        custom_resource_construct.add_policy_to_custom_resource_lambda(
            policy=aws_iam.Policy(
                self,
                "custom-resource-policy",
                document=aws_iam.PolicyDocument(
                    statements=[
                        # S3
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "s3:GetObject",
                                "s3:GetBucketLocation",
                                "s3:ListBucket",
                            ],
                            resources=[
                                environment_bucket.bucket_arn,
                                f"{environment_bucket.bucket_arn}/{proton_environment_s3_key_prefix}/*",
                            ],
                        ),
                        # Proton
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "proton:GetEnvironment",
                                "proton:UpdateEnvironment",
                                "proton:CreateEnvironment",
                                "proton:CreateEnvironmentTemplate",
                                "proton:CreateEnvironmentTemplateVersion",
                                "proton:GetEnvironmentTemplateVersion",
                                "proton:GetEnvironmentTemplateMinorVersion",
                                "proton:GetEnvironmentTemplateMajorVersion",
                                "proton:UpdateEnvironmentTemplateVersion",
                                "proton:UpdateEnvironmentTemplateMinorVersion",
                                "proton:UpdateEnvironmentTemplateMajorVersion",
                            ],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="proton",
                                    resource="environment",
                                    resource_name="cms_environment",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                                Stack.of(self).format_arn(
                                    service="proton",
                                    resource="environment-template",
                                    resource_name="cms_environment",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                            ],
                        ),
                        # IAM
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=["iam:PassRole"],
                            resources=[code_build_iam_role.role_arn],
                        ),
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=["iam:CreateServiceLinkedRole"],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="iam",
                                    resource="role",
                                    resource_name="aws-service-role/codebuild.proton.amazonaws.com/AWSServiceRoleForProtonCodeBuildProvisioning",
                                    region="",  # This is necessary since the SLR does not specify region in its ARN
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                )
                            ],
                            conditions={
                                "StringLike": {
                                    "iam:AWSServiceName": "codebuild.proton.amazonaws.com"
                                }
                            },
                        ),
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "iam:AttachRolePolicy",
                                "iam:PutRolePolicy",
                                "iam:UpdateRoleDescription",
                                "iam:DeleteServiceLinkedRole",
                                "iam:GetServiceLinkedRoleDeletionStatus",
                            ],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="iam",
                                    resource="role",
                                    resource_name="aws-service-role/codebuild.proton.amazonaws.com/AWSServiceRoleForProtonCodeBuildProvisioning",
                                    region="",  # This is necessary since the SLR does not specify region in its ARN
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                )
                            ],
                        ),
                        # KMS
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "kms:Decrypt",
                                "kms:GenerateDataKey",
                            ],
                            resources=[
                                environment_bucket.encryption_key.key_arn,  # type: ignore [union-attr]
                            ],
                        ),
                    ]
                ),
            )
        )

        create_proton_environments = CustomResource(
            self,
            "create-proton-templates",
            service_token=custom_resource_construct.custom_resource_lambda.function_arn,
            resource_type="Custom::CreateProtonEnvironment",
            properties={
                "Resource": "CreateProtonEnvironment",
                "TEMPLATE_S3_BUCKET_NAME": s3_environment_templates.deployed_bucket.bucket_name,
                "TEMPLATE_S3_KEY_PREFIX": proton_environment_s3_key_prefix,
                "CODE_BUILD_IAM_ROLE": code_build_iam_role.role_arn,
            },
        )

        create_proton_environments.node.add_dependency(s3_environment_templates)
        create_proton_environments.node.add_dependency(code_build_iam_role)
