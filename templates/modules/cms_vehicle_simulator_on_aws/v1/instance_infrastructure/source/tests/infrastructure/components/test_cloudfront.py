# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
from aws_cdk.assertions import Template

# Connected Mobility Solution on AWS
from ....infrastructure.cms_vehicle_simulator_on_aws_stack import (
    InfrastructureCloudFrontStack,
)


def test_cloudfront_s3_bucket_count(
    cloudfront_stack: InfrastructureCloudFrontStack,
) -> None:
    template = Template.from_stack(cloudfront_stack)
    template.resource_count_is("AWS::S3::Bucket", 3)


def test_cloudfront_bucket_policy_count(
    cloudfront_stack: InfrastructureCloudFrontStack,
) -> None:
    template = Template.from_stack(cloudfront_stack)
    template.resource_count_is("AWS::S3::BucketPolicy", 3)


def test_cloudfront_origin_access_identity_count(
    cloudfront_stack: InfrastructureCloudFrontStack,
) -> None:
    template = Template.from_stack(cloudfront_stack)
    template.resource_count_is("AWS::CloudFront::CloudFrontOriginAccessIdentity", 1)


def test_cloudfront_distribution_count(
    cloudfront_stack: InfrastructureCloudFrontStack,
) -> None:
    template = Template.from_stack(cloudfront_stack)
    template.resource_count_is("AWS::CloudFront::Distribution", 1)
