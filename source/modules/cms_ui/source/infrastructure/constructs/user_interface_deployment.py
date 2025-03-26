# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# AWS Libraries
from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
    aws_cloudfront,
    aws_iam,
    aws_logs,
    aws_s3,
    aws_s3_deployment,
)
from aws_solutions_constructs.aws_cloudfront_s3 import CloudFrontToS3
from constructs import Construct

# CMS Common Library
from cms_common.config.resource_names import ResourceName, ResourcePrefix
from cms_common.constructs.encrypted_s3 import EncryptedS3Construct
from cms_common.constructs.vpc_construct import VpcConstruct
from cms_common.resource_names.module_short_names import CMSModuleShortNames

# Connected Mobility Solution on AWS
from .module_integration import ModuleInputsConstruct


class UserInterfaceDeploymentConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        module_inputs: ModuleInputsConstruct,
        vpc_construct: VpcConstruct,
    ) -> None:
        super().__init__(scope, construct_id)

        app_unique_id = module_inputs.app_unique_id

        self.ui_bucket = EncryptedS3Construct(
            self,
            "cms-ui-bucket-construct",
            log_lifecycle_rules=module_inputs.s3_log_lifecycle_rules,
        )
        self.ui_bucket_prefix = "/"

        cf_logging_bucket = aws_s3.Bucket(
            self,
            "log-bucket",
            access_control=aws_s3.BucketAccessControl.LOG_DELIVERY_WRITE,
            object_ownership=aws_s3.ObjectOwnership.OBJECT_WRITER,
            block_public_access=aws_s3.BlockPublicAccess.BLOCK_ALL,
            encryption=aws_s3.BucketEncryption.S3_MANAGED,
            removal_policy=RemovalPolicy.RETAIN,
            enforce_ssl=True,
            versioned=True,
        )

        EncryptedS3Construct.add_lifecycle_to_bucket(cf_logging_bucket)

        self.ui_bucket.log_bucket.add_to_resource_policy(
            aws_iam.PolicyStatement(
                effect=aws_iam.Effect.ALLOW,
                principals=[aws_iam.ServicePrincipal("cloudfront.amazonaws.com")],
                actions=["s3:PutObject"],
                resources=[f"{self.ui_bucket.log_bucket.bucket_arn}/*"],
                conditions={
                    "StringEquals": {
                        "aws:SourceAccount": Stack.of(self).account,
                    },
                    "ArnLike": {
                        "aws:SourceArn": f"arn:aws:cloudfront::{Stack.of(self).account}:distribution/*",
                    },
                },
            )
        )

        cloudfront_response_header_policy = aws_cloudfront.ResponseHeadersPolicyProps(
            response_headers_policy_name=ResourceName.hyphen_separated(
                prefix=ResourcePrefix.hyphen_separated(
                    app_unique_id=app_unique_id,
                    module_name=CMSModuleShortNames.UI,
                ),
                name=f"{Stack.of(self).region}-response-header-policy",
            ),
            comment="Response header policy for CMS UI cloudfront distribution",
            custom_headers_behavior=aws_cloudfront.ResponseCustomHeadersBehavior(
                custom_headers=[
                    aws_cloudfront.ResponseCustomHeader(
                        header="Cache-Control",
                        override=True,
                        value="no-store, no-cache",
                    ),
                    aws_cloudfront.ResponseCustomHeader(
                        header="Pragma",
                        override=True,
                        value="no-cache",
                    ),
                ]
            ),
            security_headers_behavior=aws_cloudfront.ResponseSecurityHeadersBehavior(
                content_security_policy=aws_cloudfront.ResponseHeadersContentSecurityPolicy(
                    content_security_policy=(
                        "upgrade-insecure-requests;"
                        "default-src 'none';"
                        "media-src 'self';"
                        "object-src 'none';"
                        "base-uri 'none';"
                        "img-src 'self' https://*.amazonaws.com data: blob:;"
                        "script-src 'self';"
                        "worker-src  'self' blob:;"
                        "style-src 'self' 'unsafe-inline' https:;"
                        "connect-src 'self' wss://*.amazonaws.com https://*.amazonaws.com https://*.amazoncognito.com;"
                        "font-src 'self' https: data:;"
                        "manifest-src 'self';"
                        "frame-ancestors 'none';"
                    ),
                    override=True,
                ),
                content_type_options=aws_cloudfront.ResponseHeadersContentTypeOptions(
                    override=True
                ),
                frame_options=aws_cloudfront.ResponseHeadersFrameOptions(
                    frame_option=aws_cloudfront.HeadersFrameOption.DENY,
                    override=True,
                ),
                referrer_policy=aws_cloudfront.ResponseHeadersReferrerPolicy(
                    referrer_policy=aws_cloudfront.HeadersReferrerPolicy(
                        value=aws_cloudfront.HeadersReferrerPolicy.SAME_ORIGIN
                    ),
                    override=True,
                ),
                strict_transport_security=aws_cloudfront.ResponseHeadersStrictTransportSecurity(
                    access_control_max_age=Duration.seconds(47304000),
                    include_subdomains=True,
                    override=True,
                ),
            ),
        )

        self.cloudfront_dist = CloudFrontToS3(
            self,
            "distribution",
            existing_bucket_obj=self.ui_bucket.bucket,
            cloud_front_distribution_props={
                "comment": "CMS User Interface",
                "enableLogging": True,
                "minimumProtocolVersion": aws_cloudfront.SecurityPolicyProtocol.TLS_V1_2_2021,
                "httpVersion": aws_cloudfront.HttpVersion.HTTP2,
                "logBucket": cf_logging_bucket,
                "logFilePrefix": "frontend-cf/",
                "errorResponses": [
                    {
                        "httpStatus": 403,
                        "responseHttpStatus": 200,
                        "responsePagePath": "/index.html",
                    },
                    {
                        "httpStatus": 404,
                        "responseHttpStatus": 200,
                        "responsePagePath": "/index.html",
                    },
                ],
            },
            insert_http_security_headers=False,
            response_headers_policy_props=cloudfront_response_header_policy,
        )

        self.ui_deployment = aws_s3_deployment.BucketDeployment(
            self,
            "ui-bucket-deployment",
            sources=[aws_s3_deployment.Source.asset("./source/frontend/build")],
            exclude=["runtimeConfig.json"],
            destination_bucket=self.ui_bucket.bucket,
            destination_key_prefix=self.ui_bucket_prefix,
            prune=True,
            distribution=self.cloudfront_dist.cloud_front_web_distribution,
            distribution_paths=["/*"],
            vpc=vpc_construct.vpc,
            vpc_subnets=vpc_construct.private_subnet_selection,
            memory_limit=1024,
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
        )
