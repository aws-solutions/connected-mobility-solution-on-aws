# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any

# AWS Libraries
from aws_cdk import (
    ArnFormat,
    Aws,
    CfnMapping,
    RemovalPolicy,
    Stack,
    aws_codebuild,
    aws_codepipeline,
    aws_codepipeline_actions,
    aws_ec2,
    aws_ecr,
    aws_iam,
    aws_kms,
)
from constructs import Construct

# CMS Common Library
from cms_common.config.resource_names import get_application_level_path_prefix
from cms_common.config.stack_inputs import SolutionConfigInputs

# Connected Mobility Solution on AWS
from .backstage_assets import BackstageSourceAssetZipLocation
from .module_integration import ModuleInputsConstruct


class Pipelines(Construct):
    def __init__(  # pylint: disable=too-many-locals
        self,
        scope: Construct,
        stack_id: str,
        module_inputs: ModuleInputsConstruct,
        solution_mapping: CfnMapping,
        cloudformation_role_arn: str,
        vpc: aws_ec2.IVpc,
        private_subnet_selection: aws_ec2.SubnetSelection,
        backstage_source_asset_zip_location: BackstageSourceAssetZipLocation,
        solution_config_inputs: SolutionConfigInputs,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, stack_id, **kwargs)

        backstage_domain_input_parameters = (
            module_inputs.backstage_domain_input_parameters
        )

        self.backstage_ecr = aws_ecr.Repository(
            self,
            "backstage-ecr",
            image_scan_on_push=True,
            image_tag_mutability=aws_ecr.TagMutability.MUTABLE,
            repository_name=f"{module_inputs.acdp_uid}-backstage",
            removal_policy=RemovalPolicy.DESTROY,
        )

        backstage_artifact = aws_codepipeline.Artifact(
            artifact_name=self.backstage_ecr.repository_name
        )

        backstage_codebuild_security_group = aws_ec2.SecurityGroup(
            self,
            "backstage-codebuild-security-group",
            allow_all_outbound=True,  # NOSONAR
            vpc=vpc,
        )

        backstage_deploy_role = aws_iam.Role(
            self,
            "backstage-deploy-role",
            assumed_by=aws_iam.ServicePrincipal("codebuild.amazonaws.com"),
            description="Backstage Configuration Deploy Role",
            inline_policies={
                "s3-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "s3:PutObject",
                                "s3:GetBucketAcl",
                                "s3:GetBucketLocation",
                                "s3:GetBucketVersioning",
                                "s3:GetObject",
                                "s3:GetObjectAcl",
                                "s3:GetObjectAttributes",
                                "s3:GetObjectVersion",
                                "s3:GetObjectVersionAcl",
                                "s3:GetObjectVersionTagging",
                                "s3:ListAllMyBuckets",
                                "s3:ListBucket",
                                "s3:ListBucketVersions",
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
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
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
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "kms:Decrypt",
                                "kms:Encrypt",
                                "kms:GenerateDataKey",
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
                                "cloudformation:CreateStack",
                                "cloudformation:GetTemplateSummary",
                            ],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="cloudformation",
                                    resource="stack",
                                    resource_name=f"{module_inputs.acdp_uid}--acdp-backstage-*",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                                Stack.of(self).format_arn(
                                    service="cloudformation",
                                    resource="stack",
                                    resource_name=f"{module_inputs.acdp_uid}--acdp-backstage",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                                Stack.of(self).format_arn(
                                    service="cloudformation",
                                    resource="stack",
                                    resource_name=f"{module_inputs.acdp_uid}--acdp-backstage/*",
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
                            actions=[
                                "ssm:GetParameters",
                                "ssm:GetParameter",
                            ],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="ssm",
                                    resource="parameter",
                                    resource_name=f"{get_application_level_path_prefix(app_unique_id=module_inputs.acdp_uid, leading_slash=False)}/*",
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
                "ec2-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "ec2:DescribeVpcs",
                                "ec2:DescribeSubnets",
                                "ec2:DescribeRouteTables",
                                "ec2:DescribeVpnGateways",
                            ],
                            resources=["*"],
                        )
                    ]
                ),
                "route53-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "route53:ListHostedZonesByName",
                            ],
                            resources=["*"],
                        )
                    ]
                ),
            },
        )

        backstage_pipeline_project = aws_codebuild.PipelineProject(
            self,
            "backstage-build-pipeline-project",
            project_name="backstage-build-image",
            check_secrets_in_plain_text_env_variables=True,
            build_spec=aws_codebuild.BuildSpec.from_source_filename(
                "./source/modules/backstage/cdk/source/infrastructure/buildspecs/backstage_image_buildspec.json"
            ),
            encryption_key=aws_kms.Key(
                self, "backstage-build-key", enable_key_rotation=True
            ),
            vpc=vpc,
            subnet_selection=private_subnet_selection,
            security_groups=[backstage_codebuild_security_group],
            environment=aws_codebuild.BuildEnvironment(
                compute_type=aws_codebuild.ComputeType.LARGE,
                build_image=aws_codebuild.LinuxBuildImage.STANDARD_7_0,
                privileged=True,
            ),
            cache=aws_codebuild.Cache.local(
                aws_codebuild.LocalCacheMode.DOCKER_LAYER,
                aws_codebuild.LocalCacheMode.CUSTOM,
            ),
            environment_variables={
                "DOCKER_BUILDKIT": aws_codebuild.BuildEnvironmentVariable(
                    value=1,
                    type=aws_codebuild.BuildEnvironmentVariableType.PLAINTEXT,
                ),
                "IMAGE_NAME": aws_codebuild.BuildEnvironmentVariable(
                    value=self.backstage_ecr.repository_name,
                    type=aws_codebuild.BuildEnvironmentVariableType.PLAINTEXT,
                ),
                "IMAGE_TAG": aws_codebuild.BuildEnvironmentVariable(
                    value="latest",
                    type=aws_codebuild.BuildEnvironmentVariableType.PLAINTEXT,
                ),
                "AWS_DEFAULT_REGION": aws_codebuild.BuildEnvironmentVariable(
                    value=Stack.of(self).region,
                    type=aws_codebuild.BuildEnvironmentVariableType.PLAINTEXT,
                ),
                "AWS_ACCOUNT_ID": aws_codebuild.BuildEnvironmentVariable(
                    value=Stack.of(self).account,
                    type=aws_codebuild.BuildEnvironmentVariableType.PLAINTEXT,
                ),
                "NODE_OPTIONS": aws_codebuild.BuildEnvironmentVariable(
                    value="--max-old-space-size=8192",
                    type=aws_codebuild.BuildEnvironmentVariableType.PLAINTEXT,
                ),
            },
            role=aws_iam.Role(
                self,
                "backstage-build-role",
                assumed_by=aws_iam.ServicePrincipal("codebuild.amazonaws.com"),
                description="Backstage Build Role",
                inline_policies={
                    "backstage-build-secretsmanager-policy": aws_iam.PolicyDocument(
                        statements=[
                            aws_iam.PolicyStatement(
                                effect=aws_iam.Effect.ALLOW,
                                actions=[
                                    "secretsmanager:GetSecretValue",
                                ],
                                resources=[
                                    Stack.of(self).format_arn(
                                        service="secretsmanager",
                                        resource="secret",
                                        resource_name=f"{get_application_level_path_prefix(app_unique_id=module_inputs.acdp_uid, leading_slash=False)}/*",
                                        arn_format=ArnFormat.COLON_RESOURCE_NAME,
                                    ),
                                ],
                            ),
                        ]
                    ),
                    "backstage-build-ssm-policy": aws_iam.PolicyDocument(
                        statements=[
                            aws_iam.PolicyStatement(
                                effect=aws_iam.Effect.ALLOW,
                                actions=[
                                    "ssm:GetParameters",
                                    "ssm:GetParameter",
                                ],
                                resources=[
                                    Stack.of(self).format_arn(
                                        service="ssm",
                                        resource="parameter",
                                        resource_name=f"{get_application_level_path_prefix(app_unique_id=module_inputs.acdp_uid, leading_slash=False)}/*",
                                        arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                    ),
                                ],
                            ),
                        ]
                    ),
                },
            ),
        )
        backstage_deploy_project = aws_codebuild.PipelineProject(
            self,
            "backstage-deploy-pipeline-project",
            project_name="backstage-deploy-project",
            role=backstage_deploy_role,
            check_secrets_in_plain_text_env_variables=True,
            encryption_key=aws_kms.Key(
                self, "backstage-deploy-key", enable_key_rotation=True
            ),
            build_spec=aws_codebuild.BuildSpec.from_source_filename(
                "./source/modules/backstage/cdk/source/infrastructure/buildspecs/backstage_deploy_buildspec.json"
            ),
            vpc=vpc,
            subnet_selection=private_subnet_selection,
            security_groups=[backstage_codebuild_security_group],
            environment=aws_codebuild.BuildEnvironment(
                compute_type=aws_codebuild.ComputeType.LARGE,
                build_image=aws_codebuild.LinuxBuildImage.STANDARD_7_0,
            ),
            environment_variables={
                "ACDP_UNIQUE_ID": aws_codebuild.BuildEnvironmentVariable(
                    value=module_inputs.acdp_uid,
                    type=aws_codebuild.BuildEnvironmentVariableType.PLAINTEXT,
                ),
                "VPC_NAME": aws_codebuild.BuildEnvironmentVariable(
                    value=module_inputs.vpc_name,
                    type=aws_codebuild.BuildEnvironmentVariableType.PLAINTEXT,
                ),
                "IDENTITY_PROVIDER_ID": aws_codebuild.BuildEnvironmentVariable(
                    value=module_inputs.backstage_auth_config_inputs.identity_provider_id,
                    type=aws_codebuild.BuildEnvironmentVariableType.PLAINTEXT,
                ),
                "AWS_REGION": aws_codebuild.BuildEnvironmentVariable(
                    value=Stack.of(self).region,
                    type=aws_codebuild.BuildEnvironmentVariableType.PLAINTEXT,
                ),
                "AWS_ACCOUNT_ID": aws_codebuild.BuildEnvironmentVariable(
                    value=Stack.of(self).account,
                    type=aws_codebuild.BuildEnvironmentVariableType.PLAINTEXT,
                ),
                "NODE_OPTIONS": aws_codebuild.BuildEnvironmentVariable(
                    value="--max-old-space-size=8192",
                    type=aws_codebuild.BuildEnvironmentVariableType.PLAINTEXT,
                ),
                "CLOUDFORMATION_ROLE_ARN": aws_codebuild.BuildEnvironmentVariable(
                    value=cloudformation_role_arn,
                    type=aws_codebuild.BuildEnvironmentVariableType.PLAINTEXT,
                ),
                "SOLUTION_ID": aws_codebuild.BuildEnvironmentVariable(
                    value=solution_config_inputs.solution_id,
                    type=aws_codebuild.BuildEnvironmentVariableType.PLAINTEXT,
                ),
                "SOLUTION_VERSION": aws_codebuild.BuildEnvironmentVariable(
                    value=solution_config_inputs.solution_version,
                    type=aws_codebuild.BuildEnvironmentVariableType.PLAINTEXT,
                ),
                "SOLUTION_NAME": aws_codebuild.BuildEnvironmentVariable(
                    value=solution_config_inputs.solution_name,
                    type=aws_codebuild.BuildEnvironmentVariableType.PLAINTEXT,
                ),
                "APPLICATION_TYPE": aws_codebuild.BuildEnvironmentVariable(
                    value=solution_config_inputs.application_type,
                    type=aws_codebuild.BuildEnvironmentVariableType.PLAINTEXT,
                ),
                "REGIONAL_ASSET_BUCKET_BASE_NAME": aws_codebuild.BuildEnvironmentVariable(
                    value=solution_mapping.find_in_map(
                        "AssetsConfig", "S3AssetBucketBaseName"
                    ),
                    type=aws_codebuild.BuildEnvironmentVariableType.PLAINTEXT,
                ),
                "LOCAL_ASSET_BUCKET_NAME": aws_codebuild.BuildEnvironmentVariable(
                    value=module_inputs.local_asset_bucket_inputs.bucket_name,
                    type=aws_codebuild.BuildEnvironmentVariableType.PLAINTEXT,
                ),
                "BACKSTAGE_IMAGE_TAG": aws_codebuild.BuildEnvironmentVariable(
                    value="latest",
                    type=aws_codebuild.BuildEnvironmentVariableType.PLAINTEXT,
                ),
                "ROUTE53_HOSTED_ZONE_ID": aws_codebuild.BuildEnvironmentVariable(
                    value=backstage_domain_input_parameters.route53_hosted_zone_id_parameter.parameter_name,
                    type=aws_codebuild.BuildEnvironmentVariableType.PARAMETER_STORE,
                ),
                "FULLY_QUALIFIED_DOMAIN_NAME": aws_codebuild.BuildEnvironmentVariable(
                    value=backstage_domain_input_parameters.fully_qualified_domain_name_parameter.parameter_name,
                    type=aws_codebuild.BuildEnvironmentVariableType.PARAMETER_STORE,
                ),
                "CUSTOM_ACM_CERTIFICATE_ARN": aws_codebuild.BuildEnvironmentVariable(
                    value=backstage_domain_input_parameters.custom_acm_certificate_arn_parameter.parameter_name,
                    type=aws_codebuild.BuildEnvironmentVariableType.PARAMETER_STORE,
                ),
                "IS_PUBLIC_FACING": aws_codebuild.BuildEnvironmentVariable(
                    value=backstage_domain_input_parameters.is_public_facing_parameter.parameter_name,
                    type=aws_codebuild.BuildEnvironmentVariableType.PARAMETER_STORE,
                ),
            },
        )

        self.backstage_ecr.grant_pull_push(backstage_pipeline_project)
        self.backstage_ecr.grant(backstage_pipeline_project, "ecr:*")

        self.backstage_pipeline = aws_codepipeline.Pipeline(  # pylint: disable=unused-variable
            self,
            "backstage-code-pipeline",
            pipeline_name=f"{module_inputs.acdp_uid}-backstage-pipeline",
            enable_key_rotation=True,
            restart_execution_on_update=True,
            stages=[
                aws_codepipeline.StageOptions(
                    stage_name="Source-Stage-Backstage",
                    actions=[
                        aws_codepipeline_actions.S3SourceAction(
                            action_name="S3-Source-Backstage-Asset",
                            bucket=module_inputs.local_asset_bucket_inputs.bucket,
                            bucket_key=backstage_source_asset_zip_location.s3_object_key,
                            output=backstage_artifact,
                            trigger=aws_codepipeline_actions.S3Trigger.NONE,
                        )
                    ],
                ),
                aws_codepipeline.StageOptions(
                    stage_name="Build-Stage-Backstage",
                    actions=[
                        aws_codepipeline_actions.CodeBuildAction(
                            input=backstage_artifact,
                            action_name="Build-Image",
                            project=backstage_pipeline_project,
                            outputs=[],
                        )
                    ],
                ),
                aws_codepipeline.StageOptions(
                    stage_name="Deploy-Stage-Backstage",
                    actions=[
                        aws_codepipeline_actions.CodeBuildAction(
                            input=backstage_artifact,
                            extra_inputs=[backstage_artifact],
                            action_name="Deploy",
                            project=backstage_deploy_project,
                            outputs=[],
                        )
                    ],
                ),
            ],
            role=aws_iam.Role(
                self,
                "backstage-pipeline-role",
                assumed_by=aws_iam.ServicePrincipal("codepipeline.amazonaws.com"),
                description="Backstage Pipeline Role",
                role_name=f"{Aws.STACK_NAME}-{Stack.of(self).region}-backstage-codepipeline",
                inline_policies={
                    "backstage-s3-asset": aws_iam.PolicyDocument(
                        statements=[
                            aws_iam.PolicyStatement(
                                effect=aws_iam.Effect.ALLOW,
                                actions=[
                                    "s3:GetBucketAcl",
                                    "s3:GetBucketLocation",
                                    "s3:GetBucketVersioning",
                                    "s3:GetObject",
                                    "s3:GetObjectAcl",
                                    "s3:GetObjectAttributes",
                                    "s3:GetObjectVersion",
                                    "s3:GetObjectVersionAcl",
                                    "s3:GetObjectVersionTagging",
                                    "s3:ListAllMyBuckets",
                                    "s3:ListBucket",
                                    "s3:ListBucketVersions",
                                ],
                                resources=[
                                    Stack.of(self).format_arn(
                                        service="s3",
                                        resource=module_inputs.local_asset_bucket_inputs.bucket_name,
                                        resource_name=None,
                                        account="",
                                        region="",
                                        arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                    ),
                                    Stack.of(self).format_arn(
                                        service="s3",
                                        resource=module_inputs.local_asset_bucket_inputs.bucket_name,
                                        resource_name=backstage_source_asset_zip_location.s3_object_key,
                                        account="",
                                        region="",
                                        arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                    ),
                                ],
                            ),
                        ]
                    ),
                    "backstage-pipeline-role": aws_iam.PolicyDocument(
                        statements=[
                            aws_iam.PolicyStatement(
                                effect=aws_iam.Effect.ALLOW,
                                actions=[
                                    "secretsmanager:GetSecretValue",
                                ],
                                resources=[
                                    Stack.of(self).format_arn(
                                        service="secretsmanager",
                                        resource="secret",
                                        resource_name=f"{get_application_level_path_prefix(app_unique_id=module_inputs.acdp_uid, leading_slash=False)}/*",
                                        arn_format=ArnFormat.COLON_RESOURCE_NAME,
                                    ),
                                ],
                            ),
                        ]
                    ),
                    "backstage-pipeline-ssm-policy": aws_iam.PolicyDocument(
                        statements=[
                            aws_iam.PolicyStatement(
                                effect=aws_iam.Effect.ALLOW,
                                actions=[
                                    "ssm:GetParameter",
                                    "ssm:GetParameters",
                                ],
                                resources=[
                                    Stack.of(self).format_arn(
                                        service="ssm",
                                        resource="parameter",
                                        resource_name=f"{get_application_level_path_prefix(app_unique_id=module_inputs.acdp_uid, leading_slash=False)}/*",
                                        arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                    ),
                                ],
                            ),
                        ]
                    ),
                },
            ),
        )
