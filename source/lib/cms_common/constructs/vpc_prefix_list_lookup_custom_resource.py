# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# AWS Libraries
from aws_cdk import RemovalPolicy, Stack, aws_iam, aws_logs, custom_resources
from constructs import Construct

# Connected Mobility Solution on AWS
from ..aspects.nag_suppression import NagSuppression, NagType
from ..config.resource_names import ResourceName, ResourcePrefix
from ..policy_generators.cloudwatch import (
    generate_lambda_cloudwatch_logs_policy_document,
)
from ..policy_generators.ec2_vpc import generate_ec2_vpc_policy
from .vpc_construct import VpcConstruct


class VpcPrefixListLookupCustomResourceConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_unique_id: str,
        module_name: str,
        vpc_construct: VpcConstruct,
        prefix_list_name: str,
    ) -> None:
        super().__init__(scope, construct_id)

        function_name = ResourceName.hyphen_separated(
            ResourcePrefix.hyphen_separated(app_unique_id, module_name),
            "vpc-prefix-list-lookup",
        )

        role = aws_iam.Role(
            self,
            "vpc-prefix-list-custom-resource-role",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            inline_policies={
                "lambda-logs-policy": generate_lambda_cloudwatch_logs_policy_document(
                    self, function_name
                ),
                "ec2-policy": generate_ec2_vpc_policy(
                    self,
                    vpc_construct=vpc_construct,
                    subnet_selection=vpc_construct.private_subnet_selection,
                    authorized_service="lambda.amazonaws.com",
                ),
                "ec2-prefix-list-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "ec2:DescribeManagedPrefixLists",
                            ],
                            resources=["*"],
                            conditions={
                                "StringEquals": {
                                    "aws:PrincipalAccount": [Stack.of(self).account],
                                    "aws:RequestedRegion": [Stack.of(self).region],
                                }
                            },
                        )
                    ]
                ),
            },
        )

        prefix_list_lookup = custom_resources.AwsCustomResource(
            self,
            "vpc-endpoint-prefix-list-custom-resource",
            function_name=function_name,
            vpc=vpc_construct.vpc,  # type: ignore[arg-type]
            vpc_subnets=vpc_construct.private_subnet_selection,
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
            removal_policy=RemovalPolicy.DESTROY,
            on_create=custom_resources.AwsSdkCall(
                service="EC2",
                action="describeManagedPrefixLists",
                physical_resource_id=custom_resources.PhysicalResourceId.from_response(
                    "PrefixLists.0.PrefixListId"
                ),
                parameters={
                    "Filters": [
                        {"Name": "prefix-list-name", "Values": [prefix_list_name]}
                    ]
                },
            ),
            role=role,
            install_latest_aws_sdk=False,
        )

        self.prefix_list_id = prefix_list_lookup.get_response_field(
            "PrefixLists.0.PrefixListId"
        )

        NagSuppression.add_inline_suppression(
            node=role.node.default_child,
            suppression={
                "rules_to_suppress": [
                    {
                        "id": "AwsSolutions-IAM5",
                        "reason": "Wildcard permissions required to write to log streams.",
                    },
                ]
            },
            nag_type=NagType.CDK_NAG,
        )
