# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
from aws_cdk.assertions import Template


def test_application(cms_alerts_on_aws_stack: Template) -> None:
    cms_alerts_on_aws_stack.resource_count_is(
        "AWS::ServiceCatalogAppRegistry::Application", 1
    )


def test_attribute_group(cms_alerts_on_aws_stack: Template) -> None:
    cms_alerts_on_aws_stack.resource_count_is(
        "AWS::ServiceCatalogAppRegistry::AttributeGroup", 1
    )


def test_resource_association(cms_alerts_on_aws_stack: Template) -> None:
    cms_alerts_on_aws_stack.resource_count_is(
        "AWS::ServiceCatalogAppRegistry::ResourceAssociation", 1
    )


def test_lambda_layer_version(cms_alerts_on_aws_stack: Template) -> None:
    cms_alerts_on_aws_stack.resource_count_is("AWS::Lambda::LayerVersion", 1)


def test_kms_key(cms_alerts_on_aws_stack: Template) -> None:
    cms_alerts_on_aws_stack.resource_count_is("AWS::KMS::Key", 7)


def test_iam_role(cms_alerts_on_aws_stack: Template) -> None:
    cms_alerts_on_aws_stack.resource_count_is("AWS::IAM::Role", 10)


def test_sns_topic(cms_alerts_on_aws_stack: Template) -> None:
    cms_alerts_on_aws_stack.resource_count_is("AWS::SNS::Topic", 1)


def test_sqs_queue(cms_alerts_on_aws_stack: Template) -> None:
    cms_alerts_on_aws_stack.resource_count_is("AWS::SQS::Queue", 3)


def test_dynamodb_table(cms_alerts_on_aws_stack: Template) -> None:
    cms_alerts_on_aws_stack.resource_count_is("AWS::DynamoDB::Table", 2)


def test_lambda_function(cms_alerts_on_aws_stack: Template) -> None:
    cms_alerts_on_aws_stack.resource_count_is("AWS::Lambda::Function", 6)


def test_appsync_graphql_api(cms_alerts_on_aws_stack: Template) -> None:
    cms_alerts_on_aws_stack.resource_count_is("AWS::AppSync::GraphQLApi", 2)


def test_appsync_graphql_schema(cms_alerts_on_aws_stack: Template) -> None:
    cms_alerts_on_aws_stack.resource_count_is("AWS::AppSync::GraphQLSchema", 2)


def test_custom_log_retention(cms_alerts_on_aws_stack: Template) -> None:
    cms_alerts_on_aws_stack.resource_count_is("Custom::LogRetention", 7)


def test_iam_policy(cms_alerts_on_aws_stack: Template) -> None:
    cms_alerts_on_aws_stack.resource_count_is("AWS::IAM::Policy", 3)


def test_appsync_data_source(cms_alerts_on_aws_stack: Template) -> None:
    cms_alerts_on_aws_stack.resource_count_is("AWS::AppSync::DataSource", 2)


def test_appsync_resolver(cms_alerts_on_aws_stack: Template) -> None:
    cms_alerts_on_aws_stack.resource_count_is("AWS::AppSync::Resolver", 3)


def test_lambda_permission(cms_alerts_on_aws_stack: Template) -> None:
    cms_alerts_on_aws_stack.resource_count_is("AWS::Lambda::Permission", 3)


def test_lambda_event_source_mapping(cms_alerts_on_aws_stack: Template) -> None:
    cms_alerts_on_aws_stack.resource_count_is("AWS::Lambda::EventSourceMapping", 2)


def test_sns_subscription(cms_alerts_on_aws_stack: Template) -> None:
    cms_alerts_on_aws_stack.resource_count_is("AWS::SNS::Subscription", 1)
