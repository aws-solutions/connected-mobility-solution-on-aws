# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from functools import partial
from typing import Any, Optional, Union

# Third Party Libraries
from aws_cdk import (
    ArnFormat,
    CfnParameter,
    RemovalPolicy,
    Stack,
    aws_chatbot,
    aws_codebuild,
    aws_codepipeline,
    aws_codepipeline_actions,
    aws_ec2,
    aws_ecr,
    aws_iam,
    aws_kms,
    aws_logs,
    aws_s3_assets,
    aws_secretsmanager,
    aws_ssm,
    pipelines,
)
from constructs import Construct

# Connected Mobility Solution on AWS
from ...stacks import CmsConstants


class Pipelines(Construct):
    def __init__(  # pylint: disable=too-many-locals
        self, scope: Stack, stack_id: str, **kwargs: Any
    ) -> None:
        super().__init__(scope, stack_id, **kwargs)

        try:
            slack_chatbot_arn = CfnParameter(
                self,
                "slack-chatbot-arn",
                type="String",
                description="The Slack Chatbot ARN to send notifications to during CodePipeline stages",
                default=self.node.get_context("chatbot-configuration-arn"),
            )

            add_slack_chatbot = partial(
                self.add_slack_notification_codepipeline,
                True,
                slack_chatbot_arn.value_as_string,
            )
        except RuntimeError:
            print(
                "WARNING: Slack Chatbot ARN is not set. Notifications will not be setup."
            )
            add_slack_chatbot = partial(
                self.add_slack_notification_codepipeline, False, ""
            )

        backend_secret_object = aws_secretsmanager.Secret(  # nosec[CWE-259]
            self,
            "backend-secret",
            description="Backend secret",
            secret_name=f"{CmsConstants.STACK_NAME}/backend-secret",
            generate_secret_string=aws_secretsmanager.SecretStringGenerator(),
        )

        # Add rotation to these secrets
        # https://github.com/aws-samples/aws-secrets-manager-rotation-lambdas/blob/master/SecretsManagerRotationTemplate/lambda_function.py
        # https://gist.github.com/StevenACoffman/f0c084b428977430d2baacd0263c3563

        vpc = aws_ec2.Vpc(
            self,
            "cms-vpc",
            vpc_name=f"{CmsConstants.STACK_NAME}-vpc",
            ip_addresses=aws_ec2.IpAddresses.cidr(
                self.node.get_context("vpc-cidr-range")
            ),
            availability_zones=Stack.of(self).availability_zones,
            subnet_configuration=[
                aws_ec2.SubnetConfiguration(
                    name="application",
                    subnet_type=aws_ec2.SubnetType.PRIVATE_WITH_EGRESS,
                ),
                aws_ec2.SubnetConfiguration(
                    name="private", subnet_type=aws_ec2.SubnetType.PRIVATE_ISOLATED
                ),
                aws_ec2.SubnetConfiguration(
                    name="public", subnet_type=aws_ec2.SubnetType.PUBLIC
                ),
            ],
            nat_gateways=1,
        )

        vpc_log_group_kms_key = aws_kms.Key(
            self,
            "vpc-log-group-kms-key",
            alias="vpc-log-group-kms-key",
            enable_key_rotation=True,
        )

        vpc_log_group = aws_logs.LogGroup(
            self,
            "cms-vpc-log-group",
            removal_policy=RemovalPolicy.RETAIN,
            retention=aws_logs.RetentionDays.THREE_MONTHS,
        )

        vpc_log_group_kms_key.add_to_resource_policy(
            statement=aws_iam.PolicyStatement(
                effect=aws_iam.Effect.ALLOW,
                principals=[
                    aws_iam.ServicePrincipal(
                        f"logs.{Stack.of(self).region}.amazonaws.com"
                    )
                ],
                actions=["kms:Encrypt", "kms:Decrypt", "kms:GenerateDataKey"],
                resources=["*"],
            )
        )

        vpc.add_flow_log(
            "cms-vpc-flow-log",
            destination=aws_ec2.FlowLogDestination.to_cloud_watch_logs(
                log_group=vpc_log_group,
                iam_role=aws_iam.Role(
                    self,
                    "cms-vpc-cloudwatch-role",
                    assumed_by=aws_iam.ServicePrincipal("vpc-flow-logs.amazonaws.com"),
                    inline_policies={
                        "cms-vpc-cloudwatch-policy": aws_iam.PolicyDocument(
                            statements=[
                                aws_iam.PolicyStatement(
                                    effect=aws_iam.Effect.ALLOW,
                                    actions=[
                                        "logs:CreateLogGroup",
                                        "logs:CreateLogStream",
                                        "logs:PutLogEvents",
                                    ],
                                    resources=[
                                        vpc_log_group.log_group_arn,
                                        vpc_log_group.log_group_arn + ":log-stream:*",
                                    ],
                                ),
                            ]
                        )
                    },
                ),
            ),
        )

        # this ensures the VPC is deleted first during teardown, eliminating the deletion race condition
        vpc.node.add_dependency(vpc_log_group)

        exclude_list = [
            ".github",
            ".pytest_cache",
            ".vscode",
            "node_modules",
            "examples",
            "dist-types",
            ".git",
            "cdk.out",
            ".mypy_cache",
            ".github",
            ".venv",
            "cms_dependency_layer",
            "provisioning_dependency_layer",
            "vs_dependency_layer",
            "alerts_dependency_layer",
            "ev_battery_dependency_layer",
            "user_authentication_dependency_layer",
            "api_dependency_layer",
            "None",
            ".chalice.out",
            "staging",
            "global-s3-assets",
            "regional-s3-assets",
        ]

        backstage_zip = aws_s3_assets.Asset(
            self,
            "cms-backstage-asset",
            path="./source/backstage",
            exclude=exclude_list,
        )

        backstage_ecr = aws_ecr.Repository(
            self,
            "backstage-ecr",
            image_scan_on_push=True,
            image_tag_mutability=aws_ecr.TagMutability.MUTABLE,
            repository_name="backstage",
            removal_policy=RemovalPolicy.DESTROY,
        )
        backstage_artifact = aws_codepipeline.Artifact(artifact_name="backstage")

        assume_cdk_role = aws_iam.Role(
            self,
            "backstage-deploy-role",
            assumed_by=aws_iam.ServicePrincipal("codebuild.amazonaws.com"),
            description="Backstage Configuration Deploy Role",
            role_name=f"{CmsConstants.STACK_NAME}-{Stack.of(self).region}-backstage-config-codebuild",
            inline_policies={
                "backstage-deploy-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            resources=[
                                Stack.of(self).format_arn(
                                    region="",
                                    service="iam",
                                    resource="role",
                                    resource_name="cdk-*",
                                )
                            ],
                            actions=["sts:AssumeRole"],
                        ),
                    ]
                )
            },
        )

        backstage_configuration_deploy_project = aws_codebuild.PipelineProject(
            self,
            "backstage-env-deploy-pipeline-project",
            project_name="backstage-configuration-deploy-project",
            check_secrets_in_plain_text_env_variables=True,
            encryption_key=aws_kms.Key(
                self, "backstage-env-deploy-key", enable_key_rotation=True
            ),
            build_spec=aws_codebuild.BuildSpec.from_source_filename(
                "./cdk/source/infrastructure/buildspecs/backstage_env_buildspec.json"
            ),
            environment=aws_codebuild.BuildEnvironment(
                compute_type=aws_codebuild.ComputeType.LARGE,
                build_image=aws_codebuild.LinuxBuildImage.STANDARD_7_0,
            ),
            environment_variables={
                "BACKSTAGE_VPC_ID": aws_codebuild.BuildEnvironmentVariable(
                    value=vpc.vpc_id,
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
                "STAGE": aws_codebuild.BuildEnvironmentVariable(
                    value=CmsConstants.STAGE,
                    type=aws_codebuild.BuildEnvironmentVariableType.PLAINTEXT,
                ),
            },
            role=assume_cdk_role,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-admin-email",
            string_value=self.node.get_context("user-email"),
            description="The Cognito admin user",
            parameter_name=f"/{CmsConstants.STAGE}/{CmsConstants.APP_NAME}/admin-email",
        )
        aws_ssm.StringParameter(
            self,
            "ssm-username",
            string_value=self.node.get_context("user-email").split("@")[0],
            description="The username to access the UI",
            parameter_name=f"/{CmsConstants.STAGE}/{CmsConstants.APP_NAME}/username",
        )
        aws_ssm.StringParameter(
            self,
            "ssm-backstage-name",
            string_value=self.node.get_context("backstage-name"),
            description="The name to display on Backstage",
            parameter_name=f"/{CmsConstants.STAGE}/{CmsConstants.APP_NAME}/backstage-name",
        )
        aws_ssm.StringParameter(
            self,
            "ssm-backstage-org",
            string_value=self.node.get_context("backstage-org"),
            description="The organization to display on Backstage",
            parameter_name=f"/{CmsConstants.STAGE}/{CmsConstants.APP_NAME}/backstage-org",
        )
        aws_ssm.StringParameter(
            self,
            "ssm-backstage-log-level",
            string_value=self.node.get_context("backstage-log-level"),
            description="Level of logs to display (trace, debug, info, warn, error, critical)",
            parameter_name=f"/{CmsConstants.STAGE}/{CmsConstants.APP_NAME}/backstage-log-level",
        )
        aws_ssm.StringParameter(
            self,
            "ssm-node-env",
            string_value="production",
            description="Node context (production or development)",
            parameter_name=f"/{CmsConstants.STAGE}/{CmsConstants.APP_NAME}/node-env",
        )
        aws_ssm.StringParameter(
            self,
            "ssm-route53-zone-name",
            string_value=self.node.get_context("route53-zone-name"),
            description="The name of the hosted zone to deploy in",
            parameter_name=f"/{CmsConstants.STAGE}/{CmsConstants.APP_NAME}/route53-zone-name",
        )
        aws_ssm.StringParameter(
            self,
            "ssm-route53-base-domain",
            string_value=self.node.get_context("route53-base-domain"),
            description="The name of the base domain to deploy in",
            parameter_name=f"/{CmsConstants.STAGE}/{CmsConstants.APP_NAME}/route53-base-domain",
        )
        aws_ssm.StringParameter(
            self,
            "ssm-web-port",
            string_value=self.node.get_context("web-port"),
            description="The port used to reach Backstage (default: 443)",
            parameter_name=f"/{CmsConstants.STAGE}/{CmsConstants.APP_NAME}/web-port",
        )
        aws_ssm.StringParameter(
            self,
            "ssm-web-scheme",
            string_value=self.node.get_context("web-scheme"),
            description="The scheme used to reach Backstage (default: https)",
            parameter_name=f"/{CmsConstants.STAGE}/{CmsConstants.APP_NAME}/web-scheme",
        )
        aws_ssm.StringParameter(
            self,
            "ssm-backend-secret",
            string_value=backend_secret_object.secret_arn,
            description="Backend secret",
            parameter_name=f"/{CmsConstants.STAGE}/{CmsConstants.APP_NAME}/secret-arns/backend-secret",
        )

        backstage_pipeline_project = aws_codebuild.PipelineProject(
            self,
            "backstage-build-pipeline-project",
            project_name="backstage-build-image",
            check_secrets_in_plain_text_env_variables=True,
            build_spec=aws_codebuild.BuildSpec.from_source_filename(
                "./cdk/source/infrastructure/buildspecs/backstage_image_buildspec.json"
            ),
            encryption_key=aws_kms.Key(
                self, "backstage-build-key", enable_key_rotation=True
            ),
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
                "BACKSTAGE_NAME": aws_codebuild.BuildEnvironmentVariable(
                    value=self.node.get_context("backstage-name"),
                    type=aws_codebuild.BuildEnvironmentVariableType.PLAINTEXT,
                ),
                "BACKSTAGE_ORG": aws_codebuild.BuildEnvironmentVariable(
                    value=self.node.get_context("backstage-org"),
                    type=aws_codebuild.BuildEnvironmentVariableType.PLAINTEXT,
                ),
                "WEB_SCHEME": aws_codebuild.BuildEnvironmentVariable(
                    value=self.node.get_context("web-scheme"),
                    type=aws_codebuild.BuildEnvironmentVariableType.PLAINTEXT,
                ),
                "WEB_HOSTNAME": aws_codebuild.BuildEnvironmentVariable(
                    value=self.node.get_context("route53-zone-name"),
                    type=aws_codebuild.BuildEnvironmentVariableType.PLAINTEXT,
                ),
                "WEB_PORT": aws_codebuild.BuildEnvironmentVariable(
                    value=self.node.get_context("web-port"),
                    type=aws_codebuild.BuildEnvironmentVariableType.PLAINTEXT,
                ),
                "DOCKER_BUILDKIT": aws_codebuild.BuildEnvironmentVariable(
                    value=1,
                    type=aws_codebuild.BuildEnvironmentVariableType.PLAINTEXT,
                ),
                "BACKSTAGE_VPC_ID": aws_codebuild.BuildEnvironmentVariable(
                    value=vpc.vpc_id,
                    type=aws_codebuild.BuildEnvironmentVariableType.PLAINTEXT,
                ),
                "IMAGE_NAME": aws_codebuild.BuildEnvironmentVariable(
                    value="backstage",
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
                "STAGE": aws_codebuild.BuildEnvironmentVariable(
                    value=CmsConstants.STAGE,
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
                role_name=f"{CmsConstants.STACK_NAME}-{Stack.of(self).region}-backstage-build-codebuild",
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
                                        resource_name=f"/{CmsConstants.STAGE}/cms-backstage/*",
                                        arn_format=ArnFormat.COLON_RESOURCE_NAME,
                                    ),
                                    Stack.of(self).format_arn(
                                        service="secretsmanager",
                                        resource="secret",
                                        resource_name=f"{CmsConstants.STACK_NAME}/backend-secret",
                                        arn_format=ArnFormat.COLON_RESOURCE_NAME,
                                    ),
                                ],
                            ),
                            aws_iam.PolicyStatement(
                                effect=aws_iam.Effect.ALLOW,
                                actions=["ssm:GetParameter", "ssm:GetParameters"],
                                resources=[
                                    Stack.of(self).format_arn(
                                        service="ssm",
                                        resource="parameter",
                                        resource_name=f"{CmsConstants.STAGE}/*",
                                        arn_format=ArnFormat.SLASH_RESOURCE_NAME,
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
                                    "ssm:GetParameter",
                                ],
                                resources=[
                                    Stack.of(self).format_arn(
                                        service="ssm",
                                        resource="parameter",
                                        resource_name=f"/{CmsConstants.STAGE}/{CmsConstants.APP_NAME}/*",
                                        arn_format=ArnFormat.COLON_RESOURCE_NAME,
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
            check_secrets_in_plain_text_env_variables=True,
            encryption_key=aws_kms.Key(
                self, "backstage-deploy-key", enable_key_rotation=True
            ),
            build_spec=aws_codebuild.BuildSpec.from_source_filename(
                "./cdk/source/infrastructure/buildspecs/backstage_deploy_buildspec.json"
            ),
            environment=aws_codebuild.BuildEnvironment(
                compute_type=aws_codebuild.ComputeType.LARGE,
                build_image=aws_codebuild.LinuxBuildImage.STANDARD_7_0,
            ),
            environment_variables={
                "BACKSTAGE_VPC_ID": aws_codebuild.BuildEnvironmentVariable(
                    value=vpc.vpc_id,
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
                "BACKEND_SECRET": aws_codebuild.BuildEnvironmentVariable(
                    value=backend_secret_object.secret_arn,
                    type=aws_codebuild.BuildEnvironmentVariableType.PLAINTEXT,
                ),
                "NODE_OPTIONS": aws_codebuild.BuildEnvironmentVariable(
                    value="--max-old-space-size=8192",
                    type=aws_codebuild.BuildEnvironmentVariableType.PLAINTEXT,
                ),
                "STAGE": aws_codebuild.BuildEnvironmentVariable(
                    value=CmsConstants.STAGE,
                    type=aws_codebuild.BuildEnvironmentVariableType.PLAINTEXT,
                ),
            },
            role=assume_cdk_role,
        )

        backstage_ecr.grant_pull_push(backstage_pipeline_project)
        backstage_ecr.grant(backstage_pipeline_project, "ecr:*")

        backstage_pipeline = aws_codepipeline.Pipeline(  # pylint: disable=W0612
            self,
            "backstage-code-pipeline",
            pipeline_name="Backstage-Pipeline",
            enable_key_rotation=True,
            restart_execution_on_update=True,
            stages=[
                aws_codepipeline.StageOptions(
                    stage_name="Source-Stage-Backstage",
                    actions=[
                        aws_codepipeline_actions.S3SourceAction(
                            action_name="S3-Source-Backstage-Asset",
                            bucket_key=backstage_zip.s3_object_key,
                            bucket=backstage_zip.bucket,
                            output=backstage_artifact,
                            trigger=aws_codepipeline_actions.S3Trigger.NONE,
                        )
                    ],
                ),
                aws_codepipeline.StageOptions(
                    stage_name="Env-Deploy-Stage-Backstage",
                    actions=[
                        aws_codepipeline_actions.CodeBuildAction(
                            input=backstage_artifact,
                            extra_inputs=[],
                            action_name="Env-Deploy",
                            project=backstage_configuration_deploy_project,
                            outputs=[],
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
                role_name=f"{CmsConstants.STACK_NAME}-{Stack.of(self).region}-backstage-codepipeline",
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
                                    backstage_zip.bucket.bucket_arn,
                                    backstage_zip.bucket.arn_for_objects(
                                        backstage_zip.s3_object_key
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
                                        resource_name=f"/{CmsConstants.STAGE}/cms-backstage/*",
                                        arn_format=ArnFormat.COLON_RESOURCE_NAME,
                                    ),
                                    Stack.of(self).format_arn(
                                        service="secretsmanager",
                                        resource="secret",
                                        resource_name=f"{CmsConstants.STACK_NAME}/backend-secret",
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
                                ],
                                resources=[
                                    Stack.of(self).format_arn(
                                        service="ssm",
                                        resource="parameter",
                                        resource_name=f"/{CmsConstants.STAGE}/{CmsConstants.APP_NAME}/*",
                                        arn_format=ArnFormat.COLON_RESOURCE_NAME,
                                    ),
                                ],
                            ),
                        ]
                    ),
                },
            ),
        )

        add_slack_chatbot(backstage_pipeline)

    def add_slack_notification_codepipeline(
        self,
        is_arn_set: bool,
        slack_chatbot_arn: str,
        codepipeline: Union[aws_codepipeline.Pipeline, pipelines.CodePipeline],
    ) -> Optional[aws_chatbot.ISlackChannelConfiguration]:
        if not is_arn_set:
            return None

        pipeline: aws_codepipeline.Pipeline = getattr(
            codepipeline, "pipeline", codepipeline  # type: ignore
        )

        chatbot_target = (
            aws_chatbot.SlackChannelConfiguration.from_slack_channel_configuration_arn(
                self,
                f"{pipeline.node.id}-chatbot-arn",
                slack_channel_configuration_arn=slack_chatbot_arn,
            )
        )

        pipeline.notify_on_any_stage_state_change(
            f"{pipeline.node.id}-notify",
            target=chatbot_target,
            notification_rule_name=f"{CmsConstants.STACK_NAME}-{Stack.of(self).region}-{pipeline.pipeline_name}-notify",
        )

        return chatbot_target
