# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library

# AWS Libraries
from aws_cdk import (
    Aws,
    Stack,
    aws_certificatemanager,
    aws_cognito,
    aws_ec2,
    aws_elasticloadbalancingv2,
    aws_route53,
    aws_route53_targets,
    aws_s3,
)
from constructs import Construct

# Connected Mobility Solution on AWS
from .backstage_container import BackstageContainerConstruct
from .cognito import CognitoConstruct
from .route53 import Route53Construct

FARGATE_PORT = 443


class LoadBalancerConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        route53_construct: Route53Construct,
        backstage_container_construct: BackstageContainerConstruct,
        cognito_construct: CognitoConstruct,
        vpc: aws_ec2.IVpc,
        public_subnets: aws_ec2.SubnetSelection,
    ) -> None:
        super().__init__(scope, construct_id)

        alb_security_group = aws_ec2.SecurityGroup(
            self, "alb-security-group", vpc=vpc, allow_all_outbound=True  # NOSONAR
        )

        backstage_container_construct.fargate_security_group.add_ingress_rule(
            alb_security_group,
            connection=aws_ec2.Port.tcp(FARGATE_PORT),
            description="alb security group to fargate security group connection",
        )

        alb = aws_elasticloadbalancingv2.ApplicationLoadBalancer(
            self,
            "application-load-balancer",
            vpc=vpc,
            vpc_subnets=public_subnets,
            load_balancer_name=f"{Aws.STACK_NAME}-alb",
            security_group=alb_security_group,
            internet_facing=True,
            drop_invalid_header_fields=True,
        )

        alb_access_logs_bucket = aws_s3.Bucket(
            self,
            "alb-access-logs-bucket",
            block_public_access=aws_s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            versioned=True,
            encryption=aws_s3.BucketEncryption.S3_MANAGED,
        )

        alb.log_access_logs(
            bucket=alb_access_logs_bucket,
            prefix="backstage-alb",
        )

        listener = alb.add_listener(
            "listener",
            port=FARGATE_PORT,
            ssl_policy=aws_elasticloadbalancingv2.SslPolicy.TLS13_RES,
        )

        # ALB needs certificate in the same region as itself
        listener_certificate = aws_certificatemanager.DnsValidatedCertificate(
            self,
            "listener-certificate",
            hosted_zone=route53_construct.hosted_zone,
            region=Stack.of(self).region,
            domain_name=route53_construct.base_domain,
            subject_alternative_names=[f"*.{route53_construct.base_domain}"],
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
            targets=[backstage_container_construct.fargate_service],
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

        root_a_record = aws_route53.ARecord(
            self,
            "root-a-record",
            zone=route53_construct.hosted_zone,
            record_name=f"{route53_construct.base_domain}.",
            target=aws_route53.RecordTarget.from_alias(
                aws_route53_targets.LoadBalancerTarget(alb)
            ),
        )

        # Cognito only supports certificates in us-east-1
        cognito_certificate = aws_certificatemanager.DnsValidatedCertificate(
            self,
            "user-pool-domain-certificate",
            hosted_zone=route53_construct.hosted_zone,
            region="us-east-1",
            domain_name=route53_construct.base_domain,
            subject_alternative_names=[f"*.{route53_construct.base_domain}"],
        )

        self.user_pool_domain = cognito_construct.user_pool.add_domain(
            "user-pool-domain",
            custom_domain=aws_cognito.CustomDomainOptions(
                certificate=aws_elasticloadbalancingv2.ListenerCertificate.from_arn(  # type: ignore[arg-type]
                    cognito_certificate.certificate_arn
                ),
                domain_name=f"auth.{route53_construct.base_domain}",
            ),
        )
        self.user_pool_domain.node.add_dependency(root_a_record)

        aws_route53.ARecord(
            self,
            "cognito-a-record",
            zone=route53_construct.hosted_zone,
            record_name=f"auth.{route53_construct.base_domain}.",
            target=aws_route53.RecordTarget.from_alias(
                aws_route53_targets.UserPoolDomainTarget(self.user_pool_domain)
            ),
        )
