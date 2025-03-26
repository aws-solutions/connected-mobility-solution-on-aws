# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any, Dict

# AWS Libraries
from aws_cdk import CustomResource, aws_iam
from constructs import Construct

# CMS Common Library
from cms_common.constructs.custom_resource_lambda import CustomResourceLambdaConstruct

# Connected Mobility Solution on AWS
from ...handlers.custom_resource.function.lib.custom_resource_type_enum import (
    CustomResourceType,
)


class GrafanaDashboardConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        grafana_s3_bucket_name: str,
        grafana_s3_bucket_arn: str,
        data_sources: Dict[str, Any],
        custom_resource_lambda_construct: CustomResourceLambdaConstruct,
        dashboard_s3_object_key_prefix: str,
    ) -> None:
        super().__init__(scope, construct_id)

        grafana_dashboard_custom_resource_policy = aws_iam.Policy(
            self,
            "custom-resource-policy",
            statements=[
                aws_iam.PolicyStatement(
                    actions=[
                        "s3:PutObject",
                    ],
                    effect=aws_iam.Effect.ALLOW,
                    resources=[
                        f"{grafana_s3_bucket_arn}/{dashboard_s3_object_key_prefix}*",
                    ],
                ),
            ],
        )
        custom_resource_lambda_construct.add_policy_to_custom_resource_lambda(
            policy=grafana_dashboard_custom_resource_policy
        )

        create_dashboard_upload_to_s3_custom_resource = CustomResource(
            self,
            "create-grafana-dashboard-and-upload-to-s3-custom-resource",
            service_token=custom_resource_lambda_construct.function.function_arn,
            resource_type=f"Custom::{CustomResourceType.ResourceType.CREATE_GRAFANA_DASHBOARD_AND_UPLOAD_TO_S3.value}",
            properties={
                "Resource": CustomResourceType.ResourceType.CREATE_GRAFANA_DASHBOARD_AND_UPLOAD_TO_S3.value,
                "GrafanaS3Bucket": grafana_s3_bucket_name,
                "DashboardS3ObjectKeyPrefix": dashboard_s3_object_key_prefix,
                "DataSources": data_sources,
            },
        )
        create_dashboard_upload_to_s3_custom_resource.node.add_dependency(
            grafana_dashboard_custom_resource_policy
        )
