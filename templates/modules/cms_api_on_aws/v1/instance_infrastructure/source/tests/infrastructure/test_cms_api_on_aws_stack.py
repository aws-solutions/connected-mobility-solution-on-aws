# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
from aws_cdk.assertions import Template


def test_application(cms_api_on_aws_stack: Template) -> None:
    cms_api_on_aws_stack.resource_count_is(
        "AWS::ServiceCatalogAppRegistry::Application", 1
    )


def test_attribute_group(cms_api_on_aws_stack: Template) -> None:
    cms_api_on_aws_stack.resource_count_is(
        "AWS::ServiceCatalogAppRegistry::AttributeGroup", 1
    )


def test_resource_association(cms_api_on_aws_stack: Template) -> None:
    cms_api_on_aws_stack.resource_count_is(
        "AWS::ServiceCatalogAppRegistry::ResourceAssociation", 1
    )


def test_lambda_layer_version(cms_api_on_aws_stack: Template) -> None:
    cms_api_on_aws_stack.resource_count_is("AWS::Lambda::LayerVersion", 1)


def test_kms_key(cms_api_on_aws_stack: Template) -> None:
    cms_api_on_aws_stack.resource_count_is("AWS::KMS::Key", 1)


def test_s3_bucket(cms_api_on_aws_stack: Template) -> None:
    cms_api_on_aws_stack.resource_count_is("AWS::S3::Bucket", 2)


def test_s3_bucket_policy(cms_api_on_aws_stack: Template) -> None:
    cms_api_on_aws_stack.resource_count_is("AWS::S3::BucketPolicy", 2)


def test_iam_role(cms_api_on_aws_stack: Template) -> None:
    cms_api_on_aws_stack.resource_count_is("AWS::IAM::Role", 5)


def test_appsync_graphql_api(cms_api_on_aws_stack: Template) -> None:
    cms_api_on_aws_stack.resource_count_is("AWS::AppSync::GraphQLApi", 1)


def test_appsync_graphql_schema(cms_api_on_aws_stack: Template) -> None:
    cms_api_on_aws_stack.resource_count_is("AWS::AppSync::GraphQLSchema", 1)


def test_custom_log_retention(cms_api_on_aws_stack: Template) -> None:
    cms_api_on_aws_stack.resource_count_is("Custom::LogRetention", 2)


def test_iam_policy(cms_api_on_aws_stack: Template) -> None:
    cms_api_on_aws_stack.resource_count_is("AWS::IAM::Policy", 3)


def test_appsync_data_source(cms_api_on_aws_stack: Template) -> None:
    cms_api_on_aws_stack.resource_count_is("AWS::AppSync::DataSource", 1)


def test_appsync_resolver(cms_api_on_aws_stack: Template) -> None:
    cms_api_on_aws_stack.resource_count_is("AWS::AppSync::Resolver", 2)


def test_lambda_function(cms_api_on_aws_stack: Template) -> None:
    cms_api_on_aws_stack.resource_count_is("AWS::Lambda::Function", 3)


def test_athena_workgroup(cms_api_on_aws_stack: Template) -> None:
    cms_api_on_aws_stack.resource_count_is("AWS::Athena::WorkGroup", 1)


def test_lambda_permission(cms_api_on_aws_stack: Template) -> None:
    cms_api_on_aws_stack.resource_count_is("AWS::Lambda::Permission", 1)
