# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library

# Third Party Libraries
import aws_cdk

# Connected Mobility Solution on AWS
from ...infrastructure.stacks.cms_stack import CmsStack

app = aws_cdk.App(
    context={
        "backstage-name": "Name not set",
        "backstage-org": "Org not set",
        "user-email": "me@domain.tld",
        "github-token": "ghp_bunchofletters",
        "auth-github-client-id": "ghcid",
        "auth-github-client-secret": "ghcs",
        "gitlab-token": "glpat-bunchofletters",
        "route53-zone-name": "domain.tld",
        "route53-base-domain": "subdomain.domain.tld",
        "web-port": "443",
        "web-scheme": "https",
        "vpc-cidr-range": "10.0.0.0/16",
        "backstage-log-level": "debug",
        "cms-resource-bucket": "my-cms-bucket",
        "cms-resource-bucket-region": "us-east-1",
        "cms-resource-bucket-backstage-template-key-prefix": "v0.0.0/backstage/templates",
        "cms-resource-bucket-backstage-refresh-frequency-mins": "30",
    }
)
stack = CmsStack(app, "test-stack")
template = aws_cdk.assertions.Template.from_stack(stack)


def test_codebuild_project() -> None:
    template.has_resource("AWS::CodeBuild::Project", {})
    template.resource_count_is("AWS::CodeBuild::Project", 3)


def test_codepipeline_pipeline() -> None:
    template.has_resource("AWS::CodePipeline::Pipeline", {})
    template.resource_count_is("AWS::CodePipeline::Pipeline", 1)


def test_ec2_eip() -> None:
    template.has_resource("AWS::EC2::EIP", {})
    template.resource_count_is("AWS::EC2::EIP", 1)


def test_ec2_flowlog() -> None:
    template.has_resource("AWS::EC2::FlowLog", {})
    template.resource_count_is("AWS::EC2::FlowLog", 1)


def test_ec2_internetgateway() -> None:
    template.has_resource("AWS::EC2::InternetGateway", {})
    template.resource_count_is("AWS::EC2::InternetGateway", 1)


def test_ec2_natgateway() -> None:
    template.has_resource("AWS::EC2::NatGateway", {})
    template.resource_count_is("AWS::EC2::NatGateway", 1)


def test_ec2_route() -> None:
    template.has_resource("AWS::EC2::Route", {})
    template.resource_count_is("AWS::EC2::Route", 4)


def test_ec2_routetable() -> None:
    template.has_resource("AWS::EC2::RouteTable", {})
    template.resource_count_is("AWS::EC2::RouteTable", 6)


def test_ec2_subnet() -> None:
    template.has_resource("AWS::EC2::Subnet", {})
    template.resource_count_is("AWS::EC2::Subnet", 6)


def test_ec2_subnetroutetableassociation() -> None:
    template.has_resource("AWS::EC2::SubnetRouteTableAssociation", {})
    template.resource_count_is("AWS::EC2::SubnetRouteTableAssociation", 6)


def test_ec2_vpc() -> None:
    template.has_resource("AWS::EC2::VPC", {})
    template.resource_count_is("AWS::EC2::VPC", 1)


def test_ec2_vpcgatewayattachment() -> None:
    template.has_resource("AWS::EC2::VPCGatewayAttachment", {})
    template.resource_count_is("AWS::EC2::VPCGatewayAttachment", 1)


def test_ecr_repository() -> None:
    template.has_resource("AWS::ECR::Repository", {})
    template.resource_count_is("AWS::ECR::Repository", 1)


def test_events_rule() -> None:
    template.has_resource("AWS::Events::Rule", {})
    template.resource_count_is("AWS::Events::Rule", 1)


def test_iam_policy() -> None:
    template.has_resource("AWS::IAM::Policy", {})
    template.resource_count_is("AWS::IAM::Policy", 12)


def test_iam_role() -> None:
    template.has_resource("AWS::IAM::Role", {})
    template.resource_count_is("AWS::IAM::Role", 13)


def test_kms_alias() -> None:
    template.has_resource("AWS::KMS::Alias", {})
    template.resource_count_is("AWS::KMS::Alias", 2)


def test_kms_key() -> None:
    template.has_resource("AWS::KMS::Key", {})
    template.resource_count_is("AWS::KMS::Key", 6)


def test_logs_loggroup() -> None:
    template.has_resource("AWS::Logs::LogGroup", {})
    template.resource_count_is("AWS::Logs::LogGroup", 1)


def test_s3_bucket() -> None:
    template.has_resource("AWS::S3::Bucket", {})
    template.resource_count_is("AWS::S3::Bucket", 2)


def test_s3_bucketpolicy() -> None:
    template.has_resource("AWS::S3::BucketPolicy", {})
    template.resource_count_is("AWS::S3::BucketPolicy", 2)


def test_secretsmanager_secret() -> None:
    template.has_resource("AWS::SecretsManager::Secret", {})
    template.resource_count_is("AWS::SecretsManager::Secret", 1)
