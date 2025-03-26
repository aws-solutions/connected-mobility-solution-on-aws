# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library

# AWS Libraries
from aws_cdk import (
    Aspects,
    Aws,
    Fn,
    aws_certificatemanager,
    aws_ec2,
    aws_elasticloadbalancingv2,
    aws_route53,
    aws_route53_targets,
)
from constructs import Construct

# CMS Common Library
from cms_common.aspects.condition import ConditionAspect
from cms_common.constructs.encrypted_s3 import EncryptedS3Construct

# Connected Mobility Solution on AWS
from .backstage_container import BackstageContainerConstruct
from .module_integration import ModuleInputsConstruct

FARGATE_PORT = 443


class LoadBalancerConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        module_inputs: ModuleInputsConstruct,
        backstage_container_construct: BackstageContainerConstruct,
        vpc: aws_ec2.IVpc,
        public_subnets: aws_ec2.SubnetSelection,
        is_internet_facing: bool,
    ) -> None:
        super().__init__(scope, construct_id)

        alb = aws_elasticloadbalancingv2.ApplicationLoadBalancer(
            self,
            "application-load-balancer",
            vpc=vpc,
            vpc_subnets=public_subnets,
            load_balancer_name=f"{Aws.STACK_NAME}-alb",
            security_group=backstage_container_construct.alb_security_group,
            internet_facing=is_internet_facing,
            drop_invalid_header_fields=True,
        )

        alb_access_logs_bucket = EncryptedS3Construct.create_log_bucket(
            self,
            "alb-access-logs-bucket",
            log_lifecycle_rules=module_inputs.s3_log_lifecycle_rules,
        )

        alb.log_access_logs(
            bucket=alb_access_logs_bucket,
            prefix="backstage-alb",
        )

        listener_certificate = aws_certificatemanager.CfnCertificate(
            self,
            "listener-certificate",
            domain_name=module_inputs.dns_properties.fully_qualified_domain_name,
            validation_method="DNS",
            domain_validation_options=[
                {
                    "domainName": module_inputs.dns_properties.fully_qualified_domain_name,
                    "hostedZoneId": module_inputs.dns_properties.route53_hosted_zone_id,
                },
                {
                    "domainName": f"*.{module_inputs.dns_properties.fully_qualified_domain_name}",
                    "hostedZoneId": module_inputs.dns_properties.route53_hosted_zone_id,
                },
            ],
        )
        Aspects.of(listener_certificate).add(
            ConditionAspect(
                module_inputs.dns_properties.use_acm_dns_certificate_condition
            )
        )

        listener = alb.add_listener(
            "listener",
            port=FARGATE_PORT,
            ssl_policy=aws_elasticloadbalancingv2.SslPolicy.TLS13_RES,
            certificates=[
                aws_elasticloadbalancingv2.ListenerCertificate(
                    certificate_arn=Fn.condition_if(
                        module_inputs.dns_properties.use_custom_acm_certificate_condition.logical_id,
                        module_inputs.dns_properties.custom_acm_certificate_arn,
                        listener_certificate.ref,
                    ).to_string()
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
            zone=aws_route53.HostedZone.from_hosted_zone_id(
                self,
                "hosted-zone",
                hosted_zone_id=module_inputs.dns_properties.route53_hosted_zone_id,
            ),
            record_name=f"{module_inputs.dns_properties.fully_qualified_domain_name}.",
            target=aws_route53.RecordTarget.from_alias(
                aws_route53_targets.LoadBalancerTarget(alb)
            ),
        )

        Aspects.of(root_a_record).add(
            ConditionAspect(
                module_inputs.dns_properties.should_create_route53_records_condition
            )
        )
