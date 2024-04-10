# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0


# Connected Mobility Solution on AWS
from ..vpc_aspect import generate_ec2_vpc_policy_cfn_format, make_vpc_cfn_config


def test_make_vpc_cfn_config() -> None:
    assert make_vpc_cfn_config(
        security_group_logical_ids=["test-sec-group-1", "test-sec-group-2"],
        subnet_names=["test-subnet-1", "test-subnet-2"],
    ) == {
        "SecurityGroupIds": [
            {
                "Fn::GetAtt": [
                    "test-sec-group-1",
                    "GroupId",
                ]
            },
            {
                "Fn::GetAtt": [
                    "test-sec-group-2",
                    "GroupId",
                ]
            },
        ],
        "SubnetIds": ["test-subnet-1", "test-subnet-2"],
    }


def test_generate_ec2_vpc_policy_cfn_format() -> None:
    assert generate_ec2_vpc_policy_cfn_format(
        subnet_names=["test-subnet-1", "test-subnet-2"]
    ) == {
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
                                            "test-subnet-1",
                                        ],
                                    ]
                                },
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
                                            "test-subnet-2",
                                        ],
                                    ]
                                },
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
