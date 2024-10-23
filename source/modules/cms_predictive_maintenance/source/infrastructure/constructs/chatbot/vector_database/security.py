# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json

# AWS Libraries
from aws_cdk import CustomResource, aws_iam, aws_opensearchserverless
from constructs import Construct

# CMS Common Library
from cms_common.constructs.custom_resource_lambda import CustomResourceLambdaConstruct
from cms_common.constructs.vpc_construct import VpcConfig

# Connected Mobility Solution on AWS
from .....handlers.custom_resource.function.lib.custom_resource_type_enum import (
    CustomResourceFunctionType,
)


class VectorDBSecurityConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        custom_resource_lambda_construct: CustomResourceLambdaConstruct,
        aoss_collection_name: str,
        vpc_config: VpcConfig,
    ) -> None:
        super().__init__(scope, construct_id)

        custom_resource_policy = aws_iam.Policy(
            self,
            "custom-resource-policy",
            statements=[
                aws_iam.PolicyStatement(
                    actions=[
                        "aoss:ListVpcEndpoints",
                    ],
                    effect=aws_iam.Effect.ALLOW,
                    resources=["*"],
                ),
            ],
        )
        custom_resource_lambda_construct.add_policy_to_custom_resource_lambda(
            policy=custom_resource_policy,
        )

        get_aoss_vpc_endpoint_id = CustomResource(
            self,
            "manage-aoss-vpc-endpoint-custom-resource",
            service_token=custom_resource_lambda_construct.function.function_arn,
            resource_type=f"Custom::{CustomResourceFunctionType.GET_AOSS_VPC_ENDPOINT_ID.value}",
            properties={
                "Resource": CustomResourceFunctionType.GET_AOSS_VPC_ENDPOINT_ID.value,
                "VpcEndpointName": f"aoss-{vpc_config.vpc_id}",
            },
        )
        get_aoss_vpc_endpoint_id.node.add_dependency(custom_resource_policy)

        aoss_security_network_policy = [
            {
                "Rules": [
                    {
                        "Resource": [f"collection/{aoss_collection_name}"],
                        "ResourceType": "dashboard",
                    },
                    {
                        "Resource": [f"collection/{aoss_collection_name}"],
                        "ResourceType": "collection",
                    },
                ],
                "AllowFromPublic": False,
                "SourceVPCEs": [get_aoss_vpc_endpoint_id.get_att_string("vpce_id")],
                "SourceServices": ["bedrock.amazonaws.com"],
            }
        ]

        aws_opensearchserverless.CfnSecurityPolicy(
            self,
            "aoss-collection-network-policy",
            name=aoss_collection_name,
            type="network",
            description=f"{aoss_collection_name} - network security policy",
            policy=json.dumps(aoss_security_network_policy),
        )

        aoss_security_encryption_policy = {
            "Rules": [
                {
                    "Resource": [f"collection/{aoss_collection_name}"],
                    "ResourceType": "collection",
                }
            ],
            "AWSOwnedKey": True,
        }
        aws_opensearchserverless.CfnSecurityPolicy(
            self,
            "aoss-collection-encryption-policy",
            name=aoss_collection_name,
            type="encryption",
            description=f"{aoss_collection_name} - encryption security policy",
            policy=json.dumps(aoss_security_encryption_policy),
        )
