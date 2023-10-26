# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
import aws_cdk

# Connected Mobility Solution on AWS
from ...infrastructure.cms_connect_store_on_aws_stack import CmsConnectStoreOnAwsStack

app = aws_cdk.App()
stack = CmsConnectStoreOnAwsStack(app, "cms-connect-store-on-aws")
template = aws_cdk.assertions.Template.from_stack(stack)


def test_application() -> None:
    template.resource_count_is("AWS::ServiceCatalogAppRegistry::Application", 1)


def test_attribute_group() -> None:
    template.resource_count_is("AWS::ServiceCatalogAppRegistry::AttributeGroup", 1)


def test_attribute_group_association() -> None:
    template.resource_count_is(
        "AWS::ServiceCatalogAppRegistry::AttributeGroupAssociation", 1
    )


def test_resource_association() -> None:
    template.resource_count_is("AWS::ServiceCatalogAppRegistry::ResourceAssociation", 1)


def test_s3() -> None:
    template.has_resource("AWS::S3::Bucket", {})


def test_kms() -> None:
    template.has_resource("AWS::KMS::Key", {})


def test_roles() -> None:
    template.resource_count_is("AWS::IAM::Role", 5)


def test_aws_glue() -> None:
    template.has_resource("AWS::Glue::Database", {})
    template.resource_count_is("AWS::Glue::Schema", 1)
    template.resource_count_is("AWS::Glue::Table", 1)


def test_cms_kinesis_firehose() -> None:
    template.has_resource("AWS::KinesisFirehose::DeliveryStream", {})


def test_iot_core() -> None:
    template.resource_count_is("AWS::IoT::TopicRule", 3)


def test_lambda_function() -> None:
    template.resource_count_is("AWS::Lambda::Function", 2)
