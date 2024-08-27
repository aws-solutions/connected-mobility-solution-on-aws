# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library

# AWS Libraries
from aws_cdk import CfnOutput, CfnParameter, Stack
from constructs import Construct

# CMS Common Library
from cms_common.config.regex import RegexPattern
from cms_common.constructs.app_unique_id import AppUniqueId
from cms_common.constructs.vpc_construct import create_vpc_config, get_vpc_name

# Connected Mobility Solution on AWS
from .cloudfront import CloudFrontConstruct
from .cognito import CognitoConstruct
from .vsapi import VSApiConstruct


class ModuleInputsConstruct(Construct):
    def __init__(self, scope: Construct, construct_id: str) -> None:
        super().__init__(scope, construct_id)
        self.app_unique_id = AppUniqueId.create_cfn_parameter(Stack.of(self))

        self.admin_email = CfnParameter(
            Stack.of(self),
            "UserEmail",
            type="String",
            description="The user E-Mail to access the UI",
            allowed_pattern=RegexPattern.EMAIL,
            constraint_description="User E-Mail must be a valid E-Mail address",
        )

        self.vpc_config = create_vpc_config(
            vpc_name=get_vpc_name(self, app_unique_id=self.app_unique_id)
        )


class ModuleOutputsConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        cognito_construct: CognitoConstruct,
        cloudfront_construct: CloudFrontConstruct,
        vs_api_construct: VSApiConstruct,
        api_gateway_stage: str,
        admin_email: str,
    ) -> None:
        super().__init__(scope, construct_id)

        CfnOutput(
            Stack.of(self),
            "admin-user-email",
            description="Admin User Email",
            value=admin_email,
        )
        CfnOutput(
            Stack.of(self),
            "console-client-id",
            description="The console client ID",
            value=cognito_construct.user_pool_client.user_pool_client_id,
        )
        CfnOutput(
            Stack.of(self),
            "identity-pool-id",
            description="The ID for the Cognitio Identity Pool",
            value=cognito_construct.identity_pool.ref,
        )
        CfnOutput(
            Stack.of(self),
            "user-pool-id",
            description="User Pool Id",
            value=cognito_construct.user_pool.user_pool_id,
        )
        CfnOutput(
            Stack.of(self),
            "rest-api-id",
            description="API Gateway API ID",
            value=vs_api_construct.chalice.sam_template.get_resource("RestAPI").ref,
        )
        CfnOutput(
            Stack.of(self),
            "api-gateway-stage",
            description="API Gateway Stage",
            value=api_gateway_stage,
        )
        CfnOutput(
            Stack.of(self),
            "console-url",
            description="Console URL",
            value=f"https://{cloudfront_construct.console_cloudfront_dist.cloud_front_web_distribution.domain_name}",
        )
        CfnOutput(
            Stack.of(self),
            "cloudfront-distribution-bucket-name",
            description="Cloudfront Distribution Bucket Name",
            value=cloudfront_construct.console_cloudfront_dist.s3_bucket.bucket_name,  # type: ignore
        )
