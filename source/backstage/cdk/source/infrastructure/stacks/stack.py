# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
from textwrap import dedent
from typing import Any, List

# Third Party Libraries
from aws_cdk import (
    ArnFormat,
    Duration,
    RemovalPolicy,
    Stack,
    Tags,
    aws_certificatemanager,
    aws_cognito,
    aws_ec2,
    aws_ecr,
    aws_ecs,
    aws_elasticloadbalancingv2,
    aws_iam,
    aws_kms,
    aws_logs,
    aws_route53,
    aws_route53_targets,
    aws_s3,
    aws_secretsmanager,
    aws_ssm,
)
from constructs import Construct

# Connected Mobility Solution on AWS
from ...config.constants import BackstageConstants


class BackstageStack(Stack):
    def __init__(  # pylint: disable=R0914
        self,
        scope: Construct,
        construct_id: str,
        *args: List[Any],
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, *args, **kwargs)

        deployment_uuid = aws_ssm.StringParameter.from_string_parameter_name(
            self,
            "deployment-uuid",
            f"/{BackstageConstants.STAGE}/cms/common/config/deployment-uuid",
        ).string_value

        backstage_construct = BackstageConstruct(self, "cms-backstage")

        Tags.of(backstage_construct).add("Solutions:DeploymentUUID", deployment_uuid)


class BackstageConstruct(Construct):
    def __init__(  # pylint: disable=R0914
        self, scope: Construct, construct_id: str
    ) -> None:
        super().__init__(scope, construct_id)
        route53_zone_name = aws_ssm.StringParameter.value_from_lookup(
            self,
            f"/{BackstageConstants.STAGE}/cms/route53-zone-name",
        )

        # "dummy-value" causes failures if not removed
        if "dummy-value" in route53_zone_name:
            route53_zone_name = "test"

        route53_base_domain = aws_ssm.StringParameter.value_from_lookup(
            self,
            f"/{BackstageConstants.STAGE}/cms/route53-base-domain",
        )

        # "dummy-value" causes failures if not removed
        if "dummy-value" in route53_base_domain:
            route53_base_domain = "test"

        vpc = aws_ec2.Vpc.from_lookup(
            self,
            f"{BackstageConstants.STACK_NAME}-vpc-lookup",
            is_default=False,
            vpc_id=os.environ.get("BACKSTAGE_VPC_ID", "no_vpc_id"),
        )

        cms_backstage_name_param = aws_ssm.StringParameter.from_string_parameter_name(
            self,
            "cms-backstage-name-parameter",
            f"/{BackstageConstants.STAGE}/cms/backstage-name",
        )

        cms_backstage_org_param = aws_ssm.StringParameter.from_string_parameter_name(
            self,
            "cms-backstage-org-parameter",
            f"/{BackstageConstants.STAGE}/cms/backstage-org",
        )

        cms_resource_bucket_name_param = (
            aws_ssm.StringParameter.from_string_parameter_name(
                self,
                "cms-resource-bucket-name-parameter",
                f"/{BackstageConstants.STAGE}/common/config/cms-resource-bucket/name",
            )
        )

        cms_resource_bucket_region_param = (
            aws_ssm.StringParameter.from_string_parameter_name(
                self,
                "cms-resource-bucket-region-parameter",
                f"/{BackstageConstants.STAGE}/common/config/cms-resource-bucket/region",
            )
        )

        cms_resource_bucket_template_key_prefix_param = aws_ssm.StringParameter.from_string_parameter_name(
            self,
            "cms-resource-bucket-template-key-prefix-parameter",
            f"/{BackstageConstants.STAGE}/common/config/cms-resource-bucket/template-key-prefix",
        )

        cms_resource_bucket_template_check_freq_param = aws_ssm.StringParameter.from_string_parameter_name(
            self,
            "cms-resource-bucket-template-refresh-frequency-mins-parameter",
            f"/{BackstageConstants.STAGE}/common/config/cms-resource-bucket/refresh-frequency-mins",
        )

        backstage_catalog_bucket_name_param = aws_ssm.StringParameter.from_string_parameter_name(
            self,
            "backstage-catalog-bucket-name-parameter",
            f"/{BackstageConstants.STAGE}/{BackstageConstants.APP_NAME}/catalog-bucket/name",
        )

        backstage_catalog_bucket_region_param = aws_ssm.StringParameter.from_string_parameter_name(
            self,
            "backstage-catalog-bucket-region-parameter",
            f"/{BackstageConstants.STAGE}/{BackstageConstants.APP_NAME}/catalog-bucket/region",
        )

        backstage_catalog_bucket_key_prefix_param = aws_ssm.StringParameter.from_string_parameter_name(
            self,
            "backstage-catalog-bucket-catalog-key-prefix-parameter",
            f"/{BackstageConstants.STAGE}/{BackstageConstants.APP_NAME}/config/catalog-key-prefix",
        )

        backstage_catalog_bucket_kms_key_arn = aws_ssm.StringParameter.from_string_parameter_name(
            self,
            "backstage-catalog-bucket-kms-key-arn",
            f"/{BackstageConstants.STAGE}/{BackstageConstants.APP_NAME}/catalog-bucket/kms-key-arn",
        )

        backstage_user_pool = aws_cognito.UserPool(
            self,
            "backstage-cognito-user-pool",
            self_sign_up_enabled=False,
            advanced_security_mode=aws_cognito.AdvancedSecurityMode.ENFORCED,
            sign_in_aliases=aws_cognito.SignInAliases(
                email=True,
                username=True,
                preferred_username=True,
            ),
            standard_attributes=aws_cognito.StandardAttributes(
                email=aws_cognito.StandardAttribute(required=True, mutable=False),
                fullname=aws_cognito.StandardAttribute(required=True, mutable=True),
                preferred_username=aws_cognito.StandardAttribute(
                    required=False, mutable=True
                ),
            ),
            account_recovery=aws_cognito.AccountRecovery.EMAIL_ONLY,
            mfa=aws_cognito.Mfa.REQUIRED,
            mfa_second_factor=aws_cognito.MfaSecondFactor(sms=False, otp=True),
            user_verification=aws_cognito.UserVerificationConfig(
                email_subject="Connected Mobility Solution - Backstage - Verify your email",
                email_body="Thank you for signing up!\nClick here to verify your e-mail: {##Verify Email##}",
                email_style=aws_cognito.VerificationEmailStyle.LINK,
                sms_message="CMS Backstage\nYour verification code is {####}",
            ),
            user_invitation=aws_cognito.UserInvitationConfig(
                email_subject="Invite to join CMS Backstage!",
                email_body=dedent(
                    f"""\
                    <p>
                    Hello {{username}}, you have been invited to join CMS Backstage.<br />
                    https://{route53_base_domain}
                    </p>
                    <p>
                    Please sign in using the temporary credentials below:<br />
                    <pre>
                    Username: <strong>{{username}}</strong>
                    Password: <strong>{{####}}</strong>
                    </pre>
                    </p>
                    """
                ),
                sms_message="Hello {username}, your temporary password for CMS Backstage is {####}",
            ),
            password_policy=aws_cognito.PasswordPolicy(
                min_length=12,
                require_lowercase=True,
                require_uppercase=True,
                require_digits=True,
                require_symbols=True,
                temp_password_validity=Duration.days(1),
            ),
            device_tracking=aws_cognito.DeviceTracking(
                challenge_required_on_new_device=True,
                device_only_remembered_on_user_prompt=True,
            ),
        )
        aws_cognito.CfnUserPoolUser(
            self,
            "cognito-admin-user",
            user_pool_id=backstage_user_pool.user_pool_id,
            desired_delivery_mediums=["EMAIL"],
            force_alias_creation=True,
            user_attributes=[
                {
                    "name": "email",
                    "value": aws_ssm.StringParameter.value_for_string_parameter(
                        self,
                        f"/{BackstageConstants.STAGE}/cms/admin-email",
                    ),
                },
                {"name": "email_verified", "value": "true"},
            ],
            username=aws_ssm.StringParameter.value_for_string_parameter(
                self,
                f"/{BackstageConstants.STAGE}/cms/username",
            ),
        )

        backstage_cluster = aws_ecs.Cluster(
            self,
            "backstage-ecs-cluster",
            vpc=vpc,
            container_insights=True,
        )

        task_role = aws_iam.Role(
            self,
            "backstage-task-definition-role",
            role_name=f"{BackstageConstants.STACK_NAME}-{Stack.of(self).region}-backstage-task",
            assumed_by=aws_iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            inline_policies={
                "s3-backstage-policy": aws_iam.PolicyDocument(
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
                                    resource=cms_resource_bucket_name_param.string_value,
                                    resource_name=None,
                                    account="",
                                    region="",
                                    arn_format=ArnFormat.NO_RESOURCE_NAME,
                                ),
                                Stack.of(self).format_arn(
                                    service="s3",
                                    resource=cms_resource_bucket_name_param.string_value,
                                    resource_name="*",
                                    account="",
                                    region="",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                                Stack.of(self).format_arn(
                                    service="s3",
                                    resource=backstage_catalog_bucket_name_param.string_value,
                                    resource_name=None,
                                    account="",
                                    region="",
                                    arn_format=ArnFormat.NO_RESOURCE_NAME,
                                ),
                                Stack.of(self).format_arn(
                                    service="s3",
                                    resource=backstage_catalog_bucket_name_param.string_value,
                                    resource_name=f"{backstage_catalog_bucket_key_prefix_param.string_value}/*",
                                    account="",
                                    region="",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                            ],
                        ),
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=["s3:PutObject"],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="s3",
                                    resource=backstage_catalog_bucket_name_param.string_value,
                                    resource_name=None,
                                    account="",
                                    region="",
                                    arn_format=ArnFormat.NO_RESOURCE_NAME,
                                ),
                                Stack.of(self).format_arn(
                                    service="s3",
                                    resource=backstage_catalog_bucket_name_param.string_value,
                                    resource_name=f"{backstage_catalog_bucket_key_prefix_param.string_value}/*",
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
                            resources=[
                                backstage_catalog_bucket_kms_key_arn.string_value
                            ],
                        ),
                    ]
                ),
                "proton-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "proton:ListServiceInstances",
                            ],
                            resources=["*"],
                        ),
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "proton:GetService",
                                "proton:CreateService",
                            ],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="proton",
                                    resource="service",
                                    resource_name="*",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                )
                            ],
                        ),
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            resources=[
                                Stack.of(self).format_arn(
                                    service="codestar-connections",
                                    resource="connection",
                                    resource_name="*",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                )
                            ],
                            actions=["codestar-connections:PassConnection"],
                            conditions={
                                "StringEquals": {
                                    "codestar-connections:PassedToService": "proton.amazonaws.com"
                                }
                            },
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
                                    resource_name=backstage_user_pool.user_pool_id,
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
            "backstage-ecs-fargate-task-definition",
            cpu=1024,
            memory_limit_mib=2048,
            ephemeral_storage_gib=30,
            family=BackstageConstants.STACK_NAME,
            execution_role=task_role,
            task_role=task_role,
        )

        pg_admin = aws_secretsmanager.Secret.from_secret_name_v2(
            self,
            "backstage-pg-admin-secret",
            f"/{BackstageConstants.STAGE}/{BackstageConstants.APP_NAME}/backstage_pg_admin",
        )

        backstage_log_group_kms_key = aws_kms.Key(
            self,
            "backstage-log-group-kms-key",
            alias="backstage-log-group-kms-key",
            enable_key_rotation=True,
        )

        backstage_log_group = aws_logs.LogGroup(
            self,
            "backstage-log-group",
            removal_policy=RemovalPolicy.RETAIN,
            retention=aws_logs.RetentionDays.THREE_MONTHS,
            encryption_key=backstage_log_group_kms_key,
        )

        backstage_log_group_kms_key.add_to_resource_policy(
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
            f"{BackstageConstants.STACK_NAME}-container",
            image=aws_ecs.ContainerImage.from_ecr_repository(
                repository=aws_ecr.Repository.from_repository_name(
                    self, "backstage-ecr", "backstage"
                ),
                tag=self.node.get_context("backstage-image-tag"),
            ),
            port_mappings=[
                aws_ecs.PortMapping(
                    container_port=8080,
                    protocol=aws_ecs.Protocol.TCP,
                )
            ],
            container_name=f"{BackstageConstants.STACK_NAME}-backend",
            secrets={
                "BACKSTAGE_NAME": aws_ecs.Secret.from_ssm_parameter(
                    cms_backstage_name_param
                ),
                "BACKSTAGE_ORG": aws_ecs.Secret.from_ssm_parameter(
                    cms_backstage_org_param
                ),
                "POSTGRES_USER": aws_ecs.Secret.from_secrets_manager(
                    pg_admin, "username"
                ),
                "POSTGRES_PASSWORD": aws_ecs.Secret.from_secrets_manager(
                    pg_admin, "password"
                ),
                "POSTGRES_HOST": aws_ecs.Secret.from_secrets_manager(pg_admin, "host"),
                "POSTGRES_PORT": aws_ecs.Secret.from_secrets_manager(pg_admin, "port"),
                "BACKEND_SECRET": aws_ecs.Secret.from_secrets_manager(
                    aws_secretsmanager.Secret.from_secret_complete_arn(
                        self,
                        "backend-secret-arn",
                        secret_complete_arn=aws_ssm.StringParameter.value_for_string_parameter(
                            self,
                            f"/{BackstageConstants.STAGE}/cms/secret-arns/backend-secret",
                        ),
                    )
                ),
                "CMS_RESOURCE_BUCKET_NAME": aws_ecs.Secret.from_ssm_parameter(
                    cms_resource_bucket_name_param
                ),
                "CMS_RESOURCE_BUCKET_REGION": aws_ecs.Secret.from_ssm_parameter(
                    cms_resource_bucket_region_param
                ),
                "CMS_RESOURCE_BUCKET_TEMPLATE_KEY_PREFIX": aws_ecs.Secret.from_ssm_parameter(
                    cms_resource_bucket_template_key_prefix_param
                ),
                "CMS_RESOURCE_BUCKET_TEMPLATE_CHECK_FREQ": aws_ecs.Secret.from_ssm_parameter(
                    cms_resource_bucket_template_check_freq_param
                ),
                "BACKSTAGE_CATALOG_BUCKET_NAME": aws_ecs.Secret.from_ssm_parameter(
                    backstage_catalog_bucket_name_param
                ),
                "BACKSTAGE_CATALOG_BUCKET_REGION": aws_ecs.Secret.from_ssm_parameter(
                    backstage_catalog_bucket_region_param
                ),
                "BACKSTAGE_CATALOG_BUCKET_KEY_PREFIX": aws_ecs.Secret.from_ssm_parameter(
                    backstage_catalog_bucket_key_prefix_param
                ),
            },
            environment={
                "WEB_SCHEME": aws_ssm.StringParameter.value_for_string_parameter(
                    self,
                    f"/{BackstageConstants.STAGE}/cms/web-scheme",
                ),
                "WEB_HOSTNAME": route53_base_domain,
                "WEB_PORT": aws_ssm.StringParameter.value_for_string_parameter(
                    self,
                    f"/{BackstageConstants.STAGE}/cms/web-port",
                ),
                "BACKEND_SCHEME": aws_ssm.StringParameter.value_for_string_parameter(
                    self,
                    f"/{BackstageConstants.STAGE}/cms/web-scheme",
                ),
                "BACKEND_HOSTNAME": route53_base_domain,
                "BACKEND_PORT": aws_ssm.StringParameter.value_for_string_parameter(
                    self,
                    f"/{BackstageConstants.STAGE}/cms/web-port",
                ),
                "NODE_ENV": aws_ssm.StringParameter.value_for_string_parameter(
                    self,
                    f"/{BackstageConstants.STAGE}/cms/node-env",
                ),
                "COGNITO_USERPOOL_ID": backstage_user_pool.user_pool_id,
                "LOG_LEVEL": aws_ssm.StringParameter.value_for_string_parameter(
                    self,
                    f"/{BackstageConstants.STAGE}/cms/backstage-log-level",
                ),
            },
            logging=aws_ecs.LogDriver.aws_logs(
                log_group=backstage_log_group,
                stream_prefix=f"{BackstageConstants.STACK_NAME}-logs",
            ),
        )

        backstage_fargate_service = aws_ecs.FargateService(
            self,
            "backstage-ecs-fargate-service",
            cluster=backstage_cluster,
            task_definition=task_definition,
            service_name=f"{BackstageConstants.STACK_NAME}-fargate-service",
            desired_count=2,
            min_healthy_percent=50,
            max_healthy_percent=200,
        )

        backstage_database_security_group = aws_ec2.SecurityGroup.from_lookup_by_id(
            self,
            "backstage-database-security-group-id",
            security_group_id=aws_ssm.StringParameter.value_from_lookup(
                self,
                f"/{BackstageConstants.STAGE}/{BackstageConstants.APP_NAME}/security-groups/backstage-database-security-group-id",
            ),
        )

        backstage_database_security_group.connections.allow_from(
            other=backstage_fargate_service,
            port_range=aws_ec2.Port.tcp(5432),
            description="Allow database access from the backstage fargate service",
        )

        load_balancer = aws_elasticloadbalancingv2.ApplicationLoadBalancer(
            self,
            f"{BackstageConstants.STACK_NAME}-alb",
            vpc=vpc,
            vpc_subnets=aws_ec2.SubnetSelection(subnets=vpc.public_subnets),
            load_balancer_name=f"{BackstageConstants.STACK_NAME}-alb",
            internet_facing=True,
            drop_invalid_header_fields=True,
        )
        load_balancer.log_access_logs(
            bucket=aws_s3.Bucket(
                self,
                "backstage-elb-logs-bucket",
                block_public_access=aws_s3.BlockPublicAccess.BLOCK_ALL,
                enforce_ssl=True,
                versioned=True,
                encryption=aws_s3.BucketEncryption.S3_MANAGED,
            ),
            prefix="backstage-alb",
        )
        listener = load_balancer.add_listener(
            "listener",
            port=443,
            ssl_policy=aws_elasticloadbalancingv2.SslPolicy.TLS13_RES,
        )

        route53_zone = aws_route53.HostedZone.from_lookup(
            self,
            "backstage-route53-hosted-zone",
            domain_name=route53_zone_name,
        )

        # Cognito only supports certificates in us-east-1
        cognito_certificate = aws_certificatemanager.DnsValidatedCertificate(
            self,
            "cognito-certificate",
            hosted_zone=route53_zone,
            region="us-east-1",
            domain_name=route53_base_domain,
            subject_alternative_names=[f"*.{route53_base_domain}"],
        )

        # ALB needs certificate in the same region as itself
        listener_certificate = aws_certificatemanager.DnsValidatedCertificate(
            self,
            "alb-listener-certificate",
            hosted_zone=route53_zone,
            region=Stack.of(self).region,
            domain_name=route53_base_domain,
            subject_alternative_names=[f"*.{route53_base_domain}"],
        )

        listener.add_certificates(
            "listener-certificates",
            certificates=[
                aws_elasticloadbalancingv2.ListenerCertificate.from_arn(
                    listener_certificate.certificate_arn
                )
            ],
        )
        target_group = listener.add_targets(
            "fleet",
            port=443,
            protocol=aws_elasticloadbalancingv2.ApplicationProtocol.HTTP,
            targets=[backstage_fargate_service],
        )

        aws_elasticloadbalancingv2.ApplicationListenerRule(
            self,
            "listener-rule",
            priority=1,
            listener=listener,
            conditions=[
                aws_elasticloadbalancingv2.ListenerCondition.path_patterns(["*"])
            ],
            target_groups=[target_group],
        )

        root_record = aws_route53.ARecord(
            self,
            "backstage-route53-record",
            zone=route53_zone,
            record_name=f"{route53_base_domain}.",
            target=aws_route53.RecordTarget.from_alias(
                aws_route53_targets.LoadBalancerTarget(load_balancer)
            ),
        )

        backstage_user_pool_domain = backstage_user_pool.add_domain(
            "backstage-user-pool-domain",
            custom_domain=aws_cognito.CustomDomainOptions(
                certificate=aws_elasticloadbalancingv2.ListenerCertificate.from_arn(  # type: ignore
                    cognito_certificate.certificate_arn
                ),
                domain_name=f"auth.{route53_base_domain}",
            ),
        )
        backstage_user_pool_domain.node.add_dependency(root_record)

        aws_route53.ARecord(
            self,
            "backstage-route-to-cognito",
            zone=route53_zone,
            record_name=f"auth.{route53_base_domain}.",
            target=aws_route53.RecordTarget.from_alias(
                aws_route53_targets.UserPoolDomainTarget(backstage_user_pool_domain)
            ),
        )

        oidc_client = backstage_user_pool.add_client(
            "oidc-client",
            generate_secret=True,
            access_token_validity=Duration.hours(1),
            auth_session_validity=Duration.minutes(3),
            enable_token_revocation=True,
            id_token_validity=Duration.hours(1),
            prevent_user_existence_errors=True,
            refresh_token_validity=Duration.hours(2),
            o_auth=aws_cognito.OAuthSettings(
                flows=aws_cognito.OAuthFlows(
                    authorization_code_grant=True,
                ),
                scopes=[aws_cognito.OAuthScope.OPENID],
                callback_urls=[
                    f"https://{load_balancer.load_balancer_dns_name}/api/auth/cognito/handler/frame",
                    f"https://{load_balancer.load_balancer_dns_name}/oauth2/idpresponse",
                    f"https://{route53_base_domain}/api/auth/cognito/handler/frame",
                    f"https://{route53_base_domain}/oauth2/idpresponse",
                ],
            ),
        )
        try:
            task_definition.default_container.add_environment(  # type: ignore
                "COGNITO_CLIENT_ID", oidc_client.user_pool_client_id
            )
        except AttributeError:
            # for some reason the default container was not found
            print(
                "Default container not found, unable to add COGNITO_CLIENT_ID to the environment"
            )
