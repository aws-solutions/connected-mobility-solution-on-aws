# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

# AWS Libraries
from aws_cdk import Duration, RemovalPolicy, Stack, aws_cloudfront, aws_iam, aws_s3
from aws_solutions_constructs.aws_cloudfront_s3 import CloudFrontToS3
from constructs import Construct

# CMS Common Library
from cms_common.config.resource_names import ResourceName, ResourcePrefix
from cms_common.config.stack_inputs import SolutionConfigInputs


class CloudFrontConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        stack_id: str,
        app_unique_id: str,
        solution_config_inputs: SolutionConfigInputs,
    ) -> None:
        super().__init__(scope, stack_id)

        self.s3_logging_bucket = aws_s3.Bucket(
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

        cloudfront_response_header_policy = aws_cloudfront.ResponseHeadersPolicyProps(
            response_headers_policy_name=ResourceName.hyphen_separated(
                prefix=ResourcePrefix.hyphen_separated(
                    app_unique_id=app_unique_id,
                    module_name=solution_config_inputs.module_short_name,
                ),
                name=f"{Stack.of(self).region}-response-header-policy",
            ),
            comment="Response header policy for CMS Vehicle Simulator cloudfront distribution",
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
                        "object-src 'none';"
                        "base-uri 'none';"
                        "img-src 'self' https://*.amazonaws.com data: blob:;"
                        "script-src 'self';"
                        "style-src 'self' 'unsafe-inline' https:;"
                        "connect-src 'self' wss://*.amazonaws.com https://*.amazonaws.com;"
                        "font-src 'self' https:;"
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

        self.console_cloudfront_dist = CloudFrontToS3(
            self,
            "distribution",
            bucket_props=aws_s3.BucketProps(
                server_access_logs_bucket=self.s3_logging_bucket,
                server_access_logs_prefix="console-s3/",
                versioned=True,
                encryption=aws_s3.BucketEncryption.S3_MANAGED,
                enforce_ssl=True,
            ),
            cloud_front_distribution_props={
                "comment": "CMS Vehicle Simulator Distribution",
                "geoRestriction": aws_cloudfront.GeoRestriction.allowlist("US"),
                "enableLogging": True,
                "minimumProtocolVersion": aws_cloudfront.SecurityPolicyProtocol.TLS_V1_2_2021,
                "httpVersion": aws_cloudfront.HttpVersion.HTTP2,
                "logBucket": self.s3_logging_bucket,
                "logFilePrefix": "console-cf/",
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
            # Amusingly, insert_http_security_headers needs to be false so response_headers_policy_props can insert http security headers
            insert_http_security_headers=False,
            response_headers_policy_props=cloudfront_response_header_policy,
        )

        self.routes_bucket = aws_s3.Bucket(
            self,
            "routes-bucket",
            removal_policy=RemovalPolicy.RETAIN,
            server_access_logs_bucket=self.s3_logging_bucket,
            server_access_logs_prefix="routes-bucket-access/",
            encryption=aws_s3.BucketEncryption.S3_MANAGED,
            block_public_access=aws_s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            versioned=True,
        )

        self.routes_bucket.add_to_resource_policy(
            aws_iam.PolicyStatement(
                sid="HttpsOnly",
                resources=[
                    f"{self.routes_bucket.bucket_arn}/*",
                    f"{self.routes_bucket.bucket_arn}",
                ],
                actions=["*"],
                principals=[aws_iam.AnyPrincipal()],
                effect=aws_iam.Effect.DENY,
                conditions={"Bool": {"aws:SecureTransport": "false"}},
            )
        )
