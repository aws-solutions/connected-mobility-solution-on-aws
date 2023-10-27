# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
import aws_cdk


def test_cognito_userpool(template: aws_cdk.assertions.Template) -> None:
    template.has_resource("AWS::Cognito::UserPool", {})
    template.resource_count_is("AWS::Cognito::UserPool", 1)


def test_cognito_userpoolclient(template: aws_cdk.assertions.Template) -> None:
    template.has_resource("AWS::Cognito::UserPoolClient", {})
    template.resource_count_is("AWS::Cognito::UserPoolClient", 1)


def test_cognito_userpooldomain(template: aws_cdk.assertions.Template) -> None:
    template.has_resource("AWS::Cognito::UserPoolDomain", {})
    template.resource_count_is("AWS::Cognito::UserPoolDomain", 1)


def test_cognito_userpooluser(template: aws_cdk.assertions.Template) -> None:
    template.has_resource("AWS::Cognito::UserPoolUser", {})
    template.resource_count_is("AWS::Cognito::UserPoolUser", 1)


def test_ec2_securitygroup(template: aws_cdk.assertions.Template) -> None:
    template.has_resource("AWS::EC2::SecurityGroup", {})
    template.resource_count_is("AWS::EC2::SecurityGroup", 2)


def test_ec2_securitygroupingress(template: aws_cdk.assertions.Template) -> None:
    template.has_resource("AWS::EC2::SecurityGroupIngress", {})
    template.resource_count_is("AWS::EC2::SecurityGroupIngress", 2)


def test_ecs_cluster(template: aws_cdk.assertions.Template) -> None:
    template.has_resource("AWS::ECS::Cluster", {})
    template.resource_count_is("AWS::ECS::Cluster", 1)


def test_ecs_service(template: aws_cdk.assertions.Template) -> None:
    template.has_resource("AWS::ECS::Service", {})
    template.resource_count_is("AWS::ECS::Service", 1)


def test_ecs_taskdefinition(template: aws_cdk.assertions.Template) -> None:
    template.has_resource("AWS::ECS::TaskDefinition", {})
    template.resource_count_is("AWS::ECS::TaskDefinition", 1)


def test_elasticloadbalancingv2_listener(template: aws_cdk.assertions.Template) -> None:
    template.has_resource("AWS::ElasticLoadBalancingV2::Listener", {})
    template.resource_count_is("AWS::ElasticLoadBalancingV2::Listener", 1)


def test_elasticloadbalancingv2_listenerrule(
    template: aws_cdk.assertions.Template,
) -> None:
    template.has_resource("AWS::ElasticLoadBalancingV2::ListenerRule", {})
    template.resource_count_is("AWS::ElasticLoadBalancingV2::ListenerRule", 1)


def test_elasticloadbalancingv2_loadbalancer(
    template: aws_cdk.assertions.Template,
) -> None:
    template.has_resource("AWS::ElasticLoadBalancingV2::LoadBalancer", {})
    template.resource_count_is("AWS::ElasticLoadBalancingV2::LoadBalancer", 1)


def test_elasticloadbalancingv2_targetgroup(
    template: aws_cdk.assertions.Template,
) -> None:
    template.has_resource("AWS::ElasticLoadBalancingV2::TargetGroup", {})
    template.resource_count_is("AWS::ElasticLoadBalancingV2::TargetGroup", 1)


def test_iam_policy(template: aws_cdk.assertions.Template) -> None:
    template.has_resource("AWS::IAM::Policy", {})
    template.resource_count_is("AWS::IAM::Policy", 4)


def test_iam_role(template: aws_cdk.assertions.Template) -> None:
    template.has_resource("AWS::IAM::Role", {})
    template.resource_count_is("AWS::IAM::Role", 4)


def test_lambda_function(template: aws_cdk.assertions.Template) -> None:
    template.has_resource("AWS::Lambda::Function", {})
    template.resource_count_is("AWS::Lambda::Function", 3)


def test_logs_loggroup(template: aws_cdk.assertions.Template) -> None:
    template.has_resource("AWS::Logs::LogGroup", {})
    template.resource_count_is("AWS::Logs::LogGroup", 1)


def test_route53_recordset(template: aws_cdk.assertions.Template) -> None:
    template.has_resource("AWS::Route53::RecordSet", {})
    template.resource_count_is("AWS::Route53::RecordSet", 2)


def test_custom_userpoolcloudfrontdomainname(
    template: aws_cdk.assertions.Template,
) -> None:
    template.has_resource("Custom::UserPoolCloudFrontDomainName", {})
    template.resource_count_is("Custom::UserPoolCloudFrontDomainName", 1)


def test_security_groups_ingress_rules_are_empty_or_valid(
    template: aws_cdk.assertions.Template,
) -> None:
    allowed_tcp_ports = [80, 443]
    security_groups = template.find_resources("AWS::EC2::SecurityGroup")
    for security_group in security_groups.values():
        # when ingress rules needs to be configured, assert here that it is minimal
        ingress_rules = security_group["Properties"].get("SecurityGroupIngress", [])
        for ingress_rule in ingress_rules:
            assert ingress_rule["FromPort"] in allowed_tcp_ports
            assert ingress_rule["ToPort"] in allowed_tcp_ports
