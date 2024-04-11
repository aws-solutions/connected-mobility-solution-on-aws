# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# AWS Libraries
from aws_cdk import Duration, aws_ec2, aws_iam, aws_lambda, aws_logs
from constructs import Construct

# Connected Mobility Solution on AWS
from ..aspects.nag_suppression import NagSuppression, NagType
from ..policy_generators.cloudwatch import (
    generate_lambda_cloudwatch_logs_policy_document,
)
from ..policy_generators.ec2_vpc import generate_ec2_vpc_policy
from .vpc_construct import VpcConstruct


class CustomResourceLambdaConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        dependency_layer: aws_lambda.LayerVersion,
        unique_id: str,
        name: str,
        user_agent_string: str,
        vpc_construct: VpcConstruct,
        asset_path: str,
        suffix: str = "custom-resource",
    ) -> None:
        super().__init__(scope, construct_id)

        custom_resource_lambda_name = f"{unique_id}-{name}-{suffix}"

        self.role = aws_iam.Role(
            self,
            "lambda-role",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            inline_policies={
                "lambda-logs-policy": generate_lambda_cloudwatch_logs_policy_document(
                    self, custom_resource_lambda_name
                ),
                "ec2-policy": generate_ec2_vpc_policy(
                    self,
                    vpc_construct=vpc_construct,
                    subnet_selection=vpc_construct.private_subnet_selection,
                    authorized_service="lambda.amazonaws.com",
                ),
            },
        )

        NagSuppression.add_inline_suppression(
            node=self.role.node.default_child,
            suppression={
                "rules_to_suppress": [
                    {
                        "id": "AwsSolutions-IAM5",
                        "reason": "Wildcard permissions required to write to log streams.",
                    },
                    {
                        "id": "W11",
                        "reason": "ec2 Network Interfaces permissions need to be wildcard",
                    },
                ]
            },
            nag_type=NagType.CFN_NAG,
        )

        # Can't include unique id in the nag suppression since it is typically a Cfn ref. Wildcard it instead.
        NagSuppression.add_inline_suppression(
            node=self.role.node.default_child,
            suppression={
                "rules_to_suppress": [
                    {
                        "id": "AwsSolutions-IAM5",
                        "appliesTo": [
                            f"Resource::arn:<AWS::Partition>:logs:<AWS::Region>:<AWS::AccountId>:log-group:/aws/lambda/<AppUniqueId>-{name}-{suffix}:log-stream:*",
                            f"Resource::arn:<AWS::Partition>:logs:<AWS::Region>:<AWS::AccountId>:log-group:/aws/lambda/<AcdpUniqueId>-{name}-{suffix}:log-stream:*",
                        ],
                        "reason": "Log retention lambda uses policies that require wildcard permissions",
                    },
                    {
                        "id": "AwsSolutions-IAM5",
                        "appliesTo": [
                            "Resource::arn:<AWS::Partition>:ec2:<AWS::Region>:<AWS::AccountId>:network-interface/*",
                            "Resource::*",
                        ],
                        "reason": "ec2 Network Interfaces permissions need to be wildcard",
                    },
                ]
            },
            nag_type=NagType.CDK_NAG,
        )

        self.security_group = aws_ec2.SecurityGroup(
            self,
            "security-group",
            vpc=vpc_construct.vpc,  # type: ignore[arg-type]
            allow_all_outbound=True,  # NOSONAR
        )

        NagSuppression.add_inline_suppression(
            node=self.security_group.node.default_child,
            suppression={
                "rules_to_suppress": [
                    {
                        "id": "W40",
                        "reason": "Lambdas need outbound communication to contact other resources in VPC",
                    },
                    {
                        "id": "W5",
                        "reason": "Lambdas are inside Private Subnets and may need to communicate to services over internet. So the CIDR is wide open on egress for now",
                    },
                ]
            },
            nag_type=NagType.CFN_NAG,
        )

        self.function = aws_lambda.Function(
            self,
            "lambda-function",
            code=aws_lambda.Code.from_asset(
                asset_path,
                exclude=["**/tests/*"],
            ),
            handler="function.main.handler",
            function_name=custom_resource_lambda_name,
            role=self.role,
            runtime=aws_lambda.Runtime.PYTHON_3_10,
            timeout=Duration.minutes(5),
            layers=[dependency_layer],
            memory_size=1024,
            environment={
                "USER_AGENT_STRING": user_agent_string,
            },
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
            vpc=vpc_construct.vpc,  # type: ignore[arg-type]
            vpc_subnets=vpc_construct.private_subnet_selection,
            security_groups=[self.security_group],
        )
        NagSuppression.add_inline_suppression(
            node=self.function.node.default_child,
            suppression={
                "rules_to_suppress": [
                    {
                        "id": "AwsSolutions-L1",
                        "reason": (
                            "Some libraries used throughout the solution are not yet "
                            "supported in Python 3.11. For consistency, all lambdas are currently "
                            "kept at Python 3.10. Future refactoring of unsupported libraries will "
                            "enable the use of 3.11 throughout the solution."
                        ),
                    }
                ]
            },
            nag_type=NagType.CDK_NAG,
        )

        NagSuppression.add_inline_suppression(
            node=self.function.node.default_child,
            suppression={
                "rules_to_suppress": [
                    {
                        "id": "W92",
                        "reason": "Ignore reserved concurrent execution requirements for Lambda functions for now.",
                    },
                ]
            },
            nag_type=NagType.CFN_NAG,
        )

    def add_policy_to_custom_resource_lambda(self, policy: aws_iam.Policy) -> None:
        self.role.attach_inline_policy(policy)
