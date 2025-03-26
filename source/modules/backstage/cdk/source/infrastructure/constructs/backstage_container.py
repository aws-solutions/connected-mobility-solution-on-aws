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
    aws_logs,
    aws_secretsmanager,
)
from constructs import Construct

# CMS Common Library
from cms_common.config.multi_account import MultiAccountConfig
from cms_common.config.resource_names import ResourceName

# Connected Mobility Solution on AWS
from .aurora_database import AuroraDatabaseConstruct
from .module_integration import ModuleInputsConstruct

POSTGRES_PORT = 5432
FARGATE_PORT = 443


class BackstageContainerConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        module_inputs: ModuleInputsConstruct,
        postgres_database_construct: AuroraDatabaseConstruct,
        vpc: aws_ec2.IVpc,
        private_subnets: aws_ec2.SubnetSelection,
    ) -> None:
        super().__init__(scope, construct_id)

        backstage_task_definition_secrets = (
            module_inputs.backstage_task_definition_secrets
        )
        backstage_configuration_properties = module_inputs.backstage_configuration
        acdp_asset_config = module_inputs.acdp_asset_properties
        backstage_account_directory_secrets = (
            module_inputs.backstage_account_directory_secrets
        )

        ecs_cluster = aws_ecs.Cluster(
            self,
            "ecs-cluster",
            vpc=vpc,
            container_insights=True,
        )

        self.task_role = aws_iam.Role(
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
                                    resource_name=f"{acdp_asset_config.local_asset_bucket_entities_prefix}/*",
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
                "servicecatalog-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=["servicecatalog:GetApplication"],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="servicecatalog",
                                    resource="",
                                    resource_name="applications/*",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                            ],
                        ),
                    ]
                ),
                "costexplorer-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=["ce:GetCostAndUsage"],
                            resources=["*"],
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
            execution_role=self.task_role,
            task_role=self.task_role,
        )

        container_log_group = aws_logs.LogGroup(
            self,
            "container-log-group",
            removal_policy=RemovalPolicy.RETAIN,
            retention=aws_logs.RetentionDays.THREE_MONTHS,
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
                "USE_BACKSTAGE_AUTH_REDIRECT_FLOW": aws_ecs.Secret.from_ssm_parameter(
                    backstage_task_definition_secrets.backstage_use_auth_redirect_flow
                ),
                "BACKSTAGE_ADDITIONAL_SCOPES": aws_ecs.Secret.from_ssm_parameter(
                    backstage_task_definition_secrets.backstage_additional_scopes
                ),
                "POSTGRES_PORT": aws_ecs.Secret.from_secrets_manager(
                    postgres_database_construct.database_credentials_secret, "port"
                ),
                "CLIENT_ID": aws_ecs.Secret.from_secrets_manager(
                    module_inputs.auth_configuration_properties.user_client_config,
                    "client_id",
                ),
                "CLIENT_SECRET": aws_ecs.Secret.from_secrets_manager(
                    module_inputs.auth_configuration_properties.user_client_config,
                    "client_secret",
                ),
                "TOKEN_URL": aws_ecs.Secret.from_secrets_manager(
                    module_inputs.auth_configuration_properties.idp_config,
                    "token_endpoint",
                ),
                "AUTHORIZATION_URL": aws_ecs.Secret.from_secrets_manager(
                    module_inputs.auth_configuration_properties.idp_config,
                    "authorization_endpoint",
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
                "LOCAL_ASSET_BUCKET_ENTITIES_PREFIX": aws_ecs.Secret.from_ssm_parameter(
                    backstage_task_definition_secrets.local_asset_bucket_entities_prefix_parameter
                ),
                "LOCAL_ASSET_BUCKET_DEFAULT_ENTITIES_PREFIX": aws_ecs.Secret.from_ssm_parameter(
                    backstage_task_definition_secrets.local_asset_bucket_default_entities_prefix_parameter
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
                "DEFAULT_TARGET_ACCOUNT_ID": aws_ecs.Secret.from_ssm_parameter(
                    backstage_configuration_properties.default_target_account_id
                ),
                "DEFAULT_TARGET_REGION": aws_ecs.Secret.from_ssm_parameter(
                    backstage_configuration_properties.default_target_region
                ),
                "ENABLE_MULTI_ACCOUNT_DEPLOYMENT": aws_ecs.Secret.from_ssm_parameter(
                    backstage_account_directory_secrets.enable_multi_account_deployment
                ),
                "ORGS_MANAGEMENT_AWS_ACCOUNT_ID": aws_ecs.Secret.from_ssm_parameter(
                    backstage_account_directory_secrets.orgs_management_aws_account_id
                ),
                "ORGS_MANAGEMENT_ACCOUNT_REGION": aws_ecs.Secret.from_ssm_parameter(
                    backstage_account_directory_secrets.orgs_management_account_region
                ),
            },
            environment={
                "SOLUTION_NAME": os.environ["SOLUTION_NAME"],
                "SOLUTION_VERSION": os.environ["SOLUTION_VERSION"],
                "SOLUTION_ID": os.environ["SOLUTION_ID"],
                "SEND_ANONYMOUS_METRICS": module_inputs.send_anonymous_metrics,
                "DEPLOYMENT_UUID": module_inputs.acdp_uid,
                "METRICS_ROLE_NAME": MultiAccountConfig.METRICS_ROLE_NAME,
                "ORGS_ENROLLED_ORGS_SSM_PARAMETER_NAME": MultiAccountConfig.ENROLLED_ORGS_SSM_PARAMETER_NAME,
                "ORGS_AVAILABLE_REGIONS_SSM_PARAMETER_NAME": MultiAccountConfig.AVAILABLE_REGIONS_SSM_PARAMETER_NAME,
                "ORGS_ACCOUNT_DIRECTORY_ASSUME_ROLE_NAME": MultiAccountConfig.ORGS_ACCOUNT_DIRECTORY_ASSUME_ROLE_NAME,
                "ADMIN_USERNAME": module_inputs.admin_username,
                "WEB_HOSTNAME": module_inputs.dns_properties.fully_qualified_domain_name,
                "BACKEND_HOSTNAME": module_inputs.dns_properties.fully_qualified_domain_name,
                "NODE_ENV": backstage_configuration_properties.node_env,
                "LOG_LEVEL": backstage_configuration_properties.log_level,
                "USER_AGENT_STRING": backstage_configuration_properties.user_agent_string,
                "NODE_OPTIONS": "--no-node-snapshot",  # required by Backstage scaffolder plugin in Node20+
            },
            logging=aws_ecs.LogDriver.aws_logs(
                log_group=container_log_group,
                stream_prefix=f"{Aws.STACK_NAME}-logs",
            ),
        )

        self.fargate_security_group = aws_ec2.SecurityGroup(
            self, "fargate-security-group", vpc=vpc, allow_all_outbound=True  # NOSONAR
        )

        self.alb_security_group = aws_ec2.SecurityGroup(
            self, "alb-security-group", vpc=vpc, allow_all_outbound=True  # NOSONAR
        )

        self.fargate_security_group.add_ingress_rule(
            self.alb_security_group,
            connection=aws_ec2.Port.tcp(FARGATE_PORT),
            description="alb security group to fargate security group connection",
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
