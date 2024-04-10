# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os

# AWS Libraries
from aws_cdk import (
    ArnFormat,
    Aws,
    RemovalPolicy,
    Stack,
    aws_ec2,
    aws_ecr,
    aws_ecs,
    aws_iam,
    aws_kms,
    aws_logs,
    aws_secretsmanager,
)
from constructs import Construct

# Connected Mobility Solution on AWS
from ..lib.cms_common.config.resource_names import ResourceName
from .aurora_database import AuroraDatabaseConstruct
from .cognito import CognitoConstruct
from .module_integration import (
    ModuleInputsConstruct,
    SsmParameterWithAndWithoutSlashPrefix,
)
from .route53 import Route53Construct

POSTGRES_PORT = 5432


class BackstageContainerConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        module_inputs: ModuleInputsConstruct,
        cognito_construct: CognitoConstruct,
        postgres_database_construct: AuroraDatabaseConstruct,
        vpc: aws_ec2.IVpc,
        private_subnets: aws_ec2.SubnetSelection,
        route53_construct: Route53Construct,
    ) -> None:
        super().__init__(scope, construct_id)

        backstage_task_definition_secrets = (
            module_inputs.backstage_task_definition_secrets
        )
        backstage_configuration_properties = module_inputs.backstage_configuration
        acdp_asset_config = module_inputs.acdp_asset_properties

        ecs_cluster = aws_ecs.Cluster(
            self,
            "ecs-cluster",
            vpc=vpc,
            container_insights=True,
        )

        task_role = aws_iam.Role(
            self,
            "task-definition-role",
            role_name=f"{module_inputs.acdp_uid}-{Stack.of(self).region}-backstage-task",
            assumed_by=aws_iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            inline_policies={
                "ssm-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "ssm:GetParameter",
                                "ssm:PutParameter",
                            ],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="ssm",
                                    resource="parameter",
                                    resource_name=f"{module_inputs.acdp_build_ssm_prefix_without_slash_prefix}",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                                Stack.of(self).format_arn(
                                    service="ssm",
                                    resource="parameter",
                                    resource_name=f"{module_inputs.acdp_build_ssm_prefix_without_slash_prefix}/*",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                            ],
                        ),
                    ],
                ),
                "s3-policy": aws_iam.PolicyDocument(
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
                                    resource=acdp_asset_config.regional_asset_bucket_name,
                                    resource_name=None,
                                    account="",
                                    region="",
                                    arn_format=ArnFormat.NO_RESOURCE_NAME,
                                ),
                                Stack.of(self).format_arn(
                                    service="s3",
                                    resource=acdp_asset_config.regional_asset_bucket_name,
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
                                "s3:PutObject",
                                "s3:DeleteObject",
                                "s3:DeleteObjectVersion",
                            ],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="s3",
                                    resource=acdp_asset_config.local_asset_bucket_name,
                                    resource_name=None,
                                    account="",
                                    region="",
                                    arn_format=ArnFormat.NO_RESOURCE_NAME,
                                ),
                                Stack.of(self).format_arn(
                                    service="s3",
                                    resource=acdp_asset_config.local_asset_bucket_name,
                                    resource_name=f"{acdp_asset_config.local_asset_bucket_root_key}/*",
                                    account="",
                                    region="",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                                Stack.of(self).format_arn(
                                    service="s3",
                                    resource=acdp_asset_config.local_asset_bucket_name,
                                    resource_name=f"{acdp_asset_config.local_asset_bucket_default_assets_prefix}/*",
                                    account="",
                                    region="",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                            ],
                        ),
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "kms:GenerateDataKey",
                                "kms:Decrypt",
                                "kms:Encrypt",
                            ],
                            resources=[acdp_asset_config.local_asset_bucket_key_arn],
                        ),
                    ]
                ),
                "cognito-idp-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "cognito-idp:DescribeUserPool",
                                "cognito-idp:DescribeUserPoolClient",
                            ],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="cognito-idp",
                                    resource="userpool",
                                    resource_name=cognito_construct.user_pool.user_pool_id,
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                            ],
                        ),
                    ]
                ),
                "codebuild-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "codebuild:StartBuild",
                                "codebuild:BatchGetProjects",
                                "codebuild:BatchGetBuilds",
                                "codebuild:ListBuildsForProject",
                            ],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="codebuild",
                                    resource="project",
                                    resource_name=f"{module_inputs.acdp_uid}-*",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                            ],
                        ),
                    ]
                ),
            },
        )

        task_definition = aws_ecs.FargateTaskDefinition(
            self,
            "fargate-task-definition",
            cpu=1024,
            memory_limit_mib=2048,
            ephemeral_storage_gib=30,
            family=Aws.STACK_NAME,
            execution_role=task_role,
            task_role=task_role,
        )

        container_log_group_kms_key = aws_kms.Key(
            self,
            "container-log-group-kms-key",
            enable_key_rotation=True,
        )

        container_log_group = aws_logs.LogGroup(
            self,
            "container-log-group",
            removal_policy=RemovalPolicy.RETAIN,
            retention=aws_logs.RetentionDays.THREE_MONTHS,
            encryption_key=container_log_group_kms_key,
        )

        container_log_group_kms_key.add_to_resource_policy(
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

        task_definition.add_container(
            f"{Aws.STACK_NAME}-container",
            image=aws_ecs.ContainerImage.from_ecr_repository(
                repository=aws_ecr.Repository.from_repository_name(
                    self,
                    "ecr-repository",
                    repository_name=backstage_configuration_properties.ecr_repository_name,
                ),
                tag=os.environ["BACKSTAGE_IMAGE_TAG"],
            ),
            port_mappings=[
                aws_ecs.PortMapping(
                    container_port=8080,
                    protocol=aws_ecs.Protocol.TCP,
                )
            ],
            container_name=f"{Aws.STACK_NAME}-backend",
            secrets={  # Task definitions require ECS secrets, which can only be created from SecretsManager Secrets or SSM Parameters
                "BACKSTAGE_NAME": aws_ecs.Secret.from_ssm_parameter(
                    backstage_task_definition_secrets.backstage_name
                ),
                "BACKSTAGE_ORG": aws_ecs.Secret.from_ssm_parameter(
                    backstage_task_definition_secrets.backstage_org
                ),
                "POSTGRES_USER": aws_ecs.Secret.from_secrets_manager(
                    postgres_database_construct.database_credentials_secret, "username"
                ),
                "POSTGRES_PASSWORD": aws_ecs.Secret.from_secrets_manager(
                    postgres_database_construct.database_credentials_secret, "password"
                ),
                "POSTGRES_HOST": aws_ecs.Secret.from_secrets_manager(
                    postgres_database_construct.database_credentials_secret, "host"
                ),
                "POSTGRES_PORT": aws_ecs.Secret.from_secrets_manager(
                    postgres_database_construct.database_credentials_secret, "port"
                ),
                "BACKEND_SECRET": aws_ecs.Secret.from_secrets_manager(
                    aws_secretsmanager.Secret(
                        self,
                        "backend-secret",
                        description="Backend secret",
                        secret_name=ResourceName.slash_separated(
                            prefix=module_inputs.acdp_config_ssm_prefix_with_slash_prefix,
                            name="backstage/backend-secret",
                        ),
                        generate_secret_string=aws_secretsmanager.SecretStringGenerator(),
                    )
                ),
                "REGIONAL_ASSET_BUCKET_NAME": aws_ecs.Secret.from_ssm_parameter(
                    backstage_task_definition_secrets.regional_asset_bucket_name
                ),
                "REGIONAL_ASSET_BUCKET_REGION": aws_ecs.Secret.from_ssm_parameter(
                    backstage_task_definition_secrets.regional_asset_bucket_region
                ),
                "REGIONAL_ASSET_BUCKET_BACKSTAGE_TEMPLATE_KEY_PREFIX": aws_ecs.Secret.from_ssm_parameter(
                    backstage_task_definition_secrets.regional_asset_bucket_template_key_prefix
                ),
                "REGIONAL_ASSET_BUCKET_DISCOVERY_REFRESH_FREQ": aws_ecs.Secret.from_ssm_parameter(
                    backstage_task_definition_secrets.regional_asset_bucket_discovery_refresh_frequency
                ),
                "REGIONAL_ASSET_BUCKET_BUILDSPEC_KEY_PREFIX": aws_ecs.Secret.from_ssm_parameter(
                    backstage_task_definition_secrets.regional_asset_bucket_buildspec_key_prefix
                ),
                "LOCAL_ASSET_BUCKET_NAME": aws_ecs.Secret.from_ssm_parameter(
                    backstage_task_definition_secrets.local_asset_bucket_name
                ),
                "LOCAL_ASSET_BUCKET_REGION": aws_ecs.Secret.from_ssm_parameter(
                    backstage_task_definition_secrets.local_asset_bucket_region
                ),
                "LOCAL_ASSET_BUCKET_ROOT_KEY": aws_ecs.Secret.from_ssm_parameter(
                    backstage_task_definition_secrets.local_asset_bucket_root_key_parameter
                ),
                "LOCAL_ASSET_BUCKET_BACKSTAGE_USER_PROVIDED_TEMPLATE_KEY_PREFIX": aws_ecs.Secret.from_ssm_parameter(
                    backstage_task_definition_secrets.local_asset_bucket_backstage_user_provided_template_key_prefix
                ),
                "LOCAL_ASSET_BUCKET_BACKSTAGE_DEFAULT_TEMPLATE_KEY_PREFIX": aws_ecs.Secret.from_ssm_parameter(
                    backstage_task_definition_secrets.local_asset_bucket_backstage_default_template_key_prefix
                ),
                "LOCAL_ASSET_BUCKET_CATALOG_KEY_PREFIX": aws_ecs.Secret.from_ssm_parameter(
                    backstage_task_definition_secrets.local_asset_bucket_catalog_key_prefix
                ),
                "LOCAL_ASSET_BUCKET_TECHDOCS_KEY_PREFIX": aws_ecs.Secret.from_ssm_parameter(
                    backstage_task_definition_secrets.local_asset_bucket_techdocs_key_prefix
                ),
                "LOCAL_ASSET_BUCKET_DISCOVERY_REFRESH_FREQ": aws_ecs.Secret.from_ssm_parameter(
                    backstage_task_definition_secrets.local_asset_bucket_discovery_refresh_frequency_mins
                ),
                "CODEBUILD_PROJECT_ARN": aws_ecs.Secret.from_ssm_parameter(
                    backstage_task_definition_secrets.codebuild_project_arn
                ),
                "ACDP_BUILD_CONFIG_SSM_PREFIX": aws_ecs.Secret.from_ssm_parameter(
                    backstage_task_definition_secrets.acdp_build_config_path_root_parameter
                ),
                "TARGET_ACCOUNT_ID": aws_ecs.Secret.from_ssm_parameter(
                    SsmParameterWithAndWithoutSlashPrefix(
                        self,
                        "ssm-backstage-target-account-id",
                        path_prefix_with_slash=module_inputs.acdp_config_ssm_prefix_with_slash_prefix,
                        path_prefix_without_slash=module_inputs.acdp_config_ssm_prefix_without_slash_prefix,
                        path_postfix="deployment-targets/default/account-id",
                        create_parameter=True,
                        create_parameter_value=Stack.of(self).account,
                        create_parameter_description="Backstage Deployment Target Account Id",
                    ).parameter_without_slash_prefix
                ),
                "TARGET_REGION": aws_ecs.Secret.from_ssm_parameter(
                    SsmParameterWithAndWithoutSlashPrefix(
                        self,
                        "ssm-backstage-target-region",
                        path_prefix_with_slash=module_inputs.acdp_config_ssm_prefix_with_slash_prefix,
                        path_prefix_without_slash=module_inputs.acdp_config_ssm_prefix_without_slash_prefix,
                        path_postfix="deployment-targets/default/region",
                        create_parameter=True,
                        create_parameter_value=Stack.of(self).region,
                        create_parameter_description="Backstage Deployment Target Region",
                    ).parameter_without_slash_prefix
                ),
            },
            environment={
                "SOLUTION_NAME": os.environ["SOLUTION_NAME"],
                "SOLUTION_VERSION": os.environ["SOLUTION_VERSION"],
                "WEB_HOSTNAME": route53_construct.base_domain,
                "BACKEND_HOSTNAME": route53_construct.base_domain,
                "NODE_ENV": backstage_configuration_properties.node_env,
                "COGNITO_USERPOOL_ID": cognito_construct.user_pool.user_pool_id,
                "LOG_LEVEL": backstage_configuration_properties.log_level,
                "USER_AGENT_STRING": backstage_configuration_properties.user_agent_string,
            },
            logging=aws_ecs.LogDriver.aws_logs(
                log_group=container_log_group,
                stream_prefix=f"{Aws.STACK_NAME}-logs",
            ),
        )

        self.fargate_security_group = aws_ec2.SecurityGroup(
            self, "fargate-security-group", vpc=vpc, allow_all_outbound=True  # NOSONAR
        )

        self.fargate_service = aws_ecs.FargateService(
            self,
            "fargate-service",
            cluster=ecs_cluster,
            task_definition=task_definition,
            service_name=f"{Aws.STACK_NAME}-fargate-service",
            desired_count=2,
            assign_public_ip=False,
            min_healthy_percent=50,
            max_healthy_percent=200,
            security_groups=[self.fargate_security_group],
            vpc_subnets=private_subnets,
        )

        postgres_database_construct.database_security_group.add_ingress_rule(
            peer=self.fargate_security_group,
            connection=aws_ec2.Port.tcp(POSTGRES_PORT),
            description="Allow ingress from fargate",
        )

        task_definition.default_container.add_environment(  # type: ignore
            "COGNITO_CLIENT_ID", cognito_construct.oidc_client.user_pool_client_id
        )
