# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import re
from typing import Any, Dict, List

# Third Party Libraries
import jsii

# AWS Libraries
from aws_cdk import CfnResource, IAspect
from constructs import IConstruct


def make_vpc_cfn_config(
    security_group_logical_ids: List[str], subnet_names: List[str]
) -> Dict[str, Any]:
    return {
        "SecurityGroupIds": [
            {
                "Fn::GetAtt": [
                    security_group_logical_id,
                    "GroupId",
                ]
            }
            for security_group_logical_id in security_group_logical_ids
        ],
        "SubnetIds": subnet_names,
    }


def generate_ec2_vpc_policy_cfn_format(subnet_names: List[str]) -> Dict[str, Any]:
    return {
        "PolicyDocument": {
            "Statement": [
                {
                    "Action": [
                        "ec2:CreateNetworkInterfacePermission",
                    ],
                    "Condition": {
                        "StringEquals": {
                            "ec2:Subnet": [
                                {
                                    "Fn::Join": [
                                        "",
                                        [
                                            "arn:",
                                            {"Ref": "AWS::Partition"},
                                            ":ec2:",
                                            {"Ref": "AWS::Region"},
                                            ":",
                                            {"Ref": "AWS::AccountId"},
                                            ":subnet/",
                                            subnet_name,
                                        ],
                                    ]
                                }
                                for subnet_name in subnet_names
                            ],
                            "ec2:AuthorizedService": "lambda.amazonaws.com",
                        }
                    },
                    "Effect": "Allow",
                    "Resource": {
                        "Fn::Join": [
                            "",
                            [
                                "arn:",
                                {"Ref": "AWS::Partition"},
                                ":ec2:",
                                {"Ref": "AWS::Region"},
                                ":",
                                {"Ref": "AWS::AccountId"},
                                ":network-interface/*",
                            ],
                        ]
                    },
                },
                {
                    "Action": [
                        "ec2:DescribeNetworkInterfaces",
                        "ec2:CreateNetworkInterface",
                        "ec2:DeleteNetworkInterface",
                    ],
                    "Effect": "Allow",
                    "Resource": "*",
                },
            ],
            "Version": "2012-10-17",
        },
        "PolicyName": "ec2-policy",
    }


@jsii.implements(IAspect)
class ApplyVpcOnCustomResource:
    def __init__(
        self,
        module_name: str,
        security_group_logical_ids: List[str],
        subnet_names: List[str],
    ) -> None:
        self.vpc_config = make_vpc_cfn_config(
            security_group_logical_ids=security_group_logical_ids,
            subnet_names=subnet_names,
        )

        self.ec2_cfn_policy = generate_ec2_vpc_policy_cfn_format(
            subnet_names=subnet_names
        )

        self.service_resource_patterns = [
            rf"^/{module_name}/LogRetention[a-zA-Z0-9]+/Resource$",
            rf"^/{module_name}/AWS[a-zA-Z0-9]+/Resource$",
        ]

        self.service_role_patterns = [
            rf"^/{module_name}/LogRetention[a-zA-Z0-9]+/ServiceRole/Resource$",
            rf"^/{module_name}/AWS[a-zA-Z0-9]+/ServiceRole/Resource$",
        ]

    def visit(
        self,
        node: IConstruct,
    ) -> None:
        node_path = f"/{node.node.path}"
        vpc_config_property_path = "VpcConfig"
        policy_path = "Policies"

        if any(
            re.match(pattern, node_path) is not None
            for pattern in self.service_resource_patterns
        ):
            CfnResource.add_property_override(
                node, vpc_config_property_path, self.vpc_config  # type: ignore[arg-type]
            )
        elif any(
            re.match(pattern, node_path) is not None
            for pattern in self.service_role_patterns
        ):
            CfnResource.add_property_override(
                node,  # type: ignore[arg-type]
                policy_path,
                [self.ec2_cfn_policy],
            )
