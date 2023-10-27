# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
import aws_cdk

# Connected Mobility Solution on AWS
from ....infrastructure.stacks.env import BackstageEnvStack

app = aws_cdk.App()
stack = BackstageEnvStack(
    app,
    "test-stack",
    env=aws_cdk.Environment(
        account="test-account-id",
        region="us-west-2",
    ),
)
template = aws_cdk.assertions.Template.from_stack(stack)


def test_ec2_securitygroup() -> None:
    template.has_resource("AWS::EC2::SecurityGroup", {})
    template.resource_count_is("AWS::EC2::SecurityGroup", 2)


def test_ec2_securitygroupingress() -> None:
    template.has_resource("AWS::EC2::SecurityGroupIngress", {})
    template.resource_count_is("AWS::EC2::SecurityGroupIngress", 1)


def test_rds_dbcluster() -> None:
    template.has_resource("AWS::RDS::DBCluster", {})
    template.resource_count_is("AWS::RDS::DBCluster", 1)


def test_rds_dbsubnetgroup() -> None:
    template.has_resource("AWS::RDS::DBSubnetGroup", {})
    template.resource_count_is("AWS::RDS::DBSubnetGroup", 1)


def test_secretsmanager_secret() -> None:
    template.has_resource("AWS::SecretsManager::Secret", {})
    template.resource_count_is("AWS::SecretsManager::Secret", 1)


def test_secretsmanager_secrettargetattachment() -> None:
    template.has_resource("AWS::SecretsManager::SecretTargetAttachment", {})
    template.resource_count_is("AWS::SecretsManager::SecretTargetAttachment", 1)


def test_security_groups_ingress_rules_are_empty() -> None:
    security_groups = template.find_resources("AWS::EC2::SecurityGroup")
    for security_group in security_groups.values():
        # assert that no ingress rules are configured
        # when ingress rules needs to be configured, assert here that it is minimal
        assert not security_group["Properties"].get("SecurityGroupIngress")
