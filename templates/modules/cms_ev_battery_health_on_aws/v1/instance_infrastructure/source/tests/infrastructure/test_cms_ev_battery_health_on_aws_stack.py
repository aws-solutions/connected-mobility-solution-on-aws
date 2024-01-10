# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
import aws_cdk
from aws_cdk.assertions import Template

# Connected Mobility Solution on AWS
from ...infrastructure.cms_ev_battery_health_on_aws_stack import (
    CmsEVBatteryHealthOnAwsStack,
)

app = aws_cdk.App()
stack = CmsEVBatteryHealthOnAwsStack(app, "cms-ev-battery-health-on-aws")
template = Template.from_stack(stack)


def test_grafana_workspace() -> None:
    template.has_resource("AWS::Grafana::Workspace", {})
    template.resource_count_is("AWS::Grafana::Workspace", 1)


def test_iam_policy() -> None:
    template.has_resource("AWS::IAM::Policy", {})
    template.resource_count_is("AWS::IAM::Policy", 16)


def test_iam_role() -> None:
    template.has_resource("AWS::IAM::Role", {})
    template.resource_count_is("AWS::IAM::Role", 13)


def test_kms_key() -> None:
    template.has_resource("AWS::KMS::Key", {})
    template.resource_count_is("AWS::KMS::Key", 3)


def test_lambda_function() -> None:
    template.has_resource("AWS::Lambda::Function", {})
    template.resource_count_is("AWS::Lambda::Function", 11)


def test_lambda_layerversion() -> None:
    template.has_resource("AWS::Lambda::LayerVersion", {})
    template.resource_count_is("AWS::Lambda::LayerVersion", 1)


def test_lambda_permission() -> None:
    template.has_resource("AWS::Lambda::Permission", {})
    template.resource_count_is("AWS::Lambda::Permission", 4)


def test_s3_bucket() -> None:
    template.has_resource("AWS::S3::Bucket", {})
    template.resource_count_is("AWS::S3::Bucket", 2)


def test_s3_bucketpolicy() -> None:
    template.has_resource("AWS::S3::BucketPolicy", {})
    template.resource_count_is("AWS::S3::BucketPolicy", 2)


def test_secretsmanager_resourcepolicy() -> None:
    template.has_resource("AWS::SecretsManager::ResourcePolicy", {})
    template.resource_count_is("AWS::SecretsManager::ResourcePolicy", 1)


def test_secretsmanager_rotationschedule() -> None:
    template.has_resource("AWS::SecretsManager::RotationSchedule", {})
    template.resource_count_is("AWS::SecretsManager::RotationSchedule", 1)


def test_secretsmanager_secret() -> None:
    template.has_resource("AWS::SecretsManager::Secret", {})
    template.resource_count_is("AWS::SecretsManager::Secret", 1)


def test_servicecatalogappregistry_application() -> None:
    template.has_resource("AWS::ServiceCatalogAppRegistry::Application", {})
    template.resource_count_is("AWS::ServiceCatalogAppRegistry::Application", 1)


def test_servicecatalogappregistry_attributegroup() -> None:
    template.has_resource("AWS::ServiceCatalogAppRegistry::AttributeGroup", {})
    template.resource_count_is("AWS::ServiceCatalogAppRegistry::AttributeGroup", 1)


def test_servicecatalogappregistry_attributegroupassociation() -> None:
    template.has_resource(
        "AWS::ServiceCatalogAppRegistry::AttributeGroupAssociation", {}
    )
    template.resource_count_is(
        "AWS::ServiceCatalogAppRegistry::AttributeGroupAssociation", 1
    )


def test_servicecatalogappregistry_resourceassociation() -> None:
    template.has_resource("AWS::ServiceCatalogAppRegistry::ResourceAssociation", {})
    template.resource_count_is("AWS::ServiceCatalogAppRegistry::ResourceAssociation", 1)


def test_custom_creategrafanaapikey() -> None:
    template.has_resource("Custom::CreateGrafanaApiKey", {})
    template.resource_count_is("Custom::CreateGrafanaApiKey", 1)


def test_custom_creategrafanadashboardanduploadtos3() -> None:
    template.has_resource("Custom::CreateGrafanaDashboardAndUploadToS3", {})
    template.resource_count_is("Custom::CreateGrafanaDashboardAndUploadToS3", 1)


def test_custom_creategrafanadatasource() -> None:
    template.has_resource("Custom::CreateGrafanaDataSource", {})
    template.resource_count_is("Custom::CreateGrafanaDataSource", 1)


def test_custom_logretention() -> None:
    template.has_resource("Custom::LogRetention", {})
    template.resource_count_is("Custom::LogRetention", 8)


def test_custom_s3autodeleteobjects() -> None:
    template.has_resource("Custom::S3AutoDeleteObjects", {})
    template.resource_count_is("Custom::S3AutoDeleteObjects", 1)


def test_custom_s3bucketnotifications() -> None:
    template.has_resource("Custom::S3BucketNotifications", {})
    template.resource_count_is("Custom::S3BucketNotifications", 1)
