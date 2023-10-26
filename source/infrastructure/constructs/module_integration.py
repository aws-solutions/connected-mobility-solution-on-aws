# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import cast

# Third Party Libraries
from aws_cdk import CfnCondition, CfnResource, aws_ssm
from constructs import Construct

# Connected Mobility Solution on AWS
from ..stacks import CmsConstants


class ModuleOutputsConstruct(Construct):
    # pylint: disable=too-many-arguments
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        deployment_uuid: str,
        resource_bucket: str,
        resource_bucket_region: str,
        resource_bucket_key_prefix: str,
        resource_bucket_refresh_frequency_min: str,
        metrics_url: str,
        send_anonymous_usage: str,
        send_anonymous_usage_condition: CfnCondition,
    ) -> None:
        super().__init__(scope, construct_id)

        aws_ssm.StringParameter(
            self,
            "ssm-cms-deployment-uuid",
            string_value=deployment_uuid,
            description="Solution UUID used to tag resources within CMS",
            parameter_name=f"/{CmsConstants.STAGE}/cms/common/config/deployment-uuid",
        )

        aws_ssm.StringParameter(
            self,
            "ssm-cms-resource-bucket",
            string_value=resource_bucket,
            description="Bucket name where CMS Resources are to be accessed from",
            parameter_name=f"/{CmsConstants.STAGE}/common/config/cms-resource-bucket/name",
        )

        aws_ssm.StringParameter(
            self,
            "ssm-cms-resource-bucket-region",
            string_value=resource_bucket_region,
            description="Bucket region where CMS Resources are to be accessed from",
            parameter_name=f"/{CmsConstants.STAGE}/common/config/cms-resource-bucket/region",
        )

        aws_ssm.StringParameter(
            self,
            "ssm-cms-resource-bucket-backstage-template-key-prefix",
            string_value=resource_bucket_key_prefix,
            description="Bucket key prefix where CMS Resources are to be accessed from",
            parameter_name=f"/{CmsConstants.STAGE}/common/config/cms-resource-bucket/template-key-prefix",
        )

        aws_ssm.StringParameter(
            self,
            "ssm-cms-resource-bucket-backstage-template-refresh-freq-mins",
            string_value=resource_bucket_refresh_frequency_min,
            description="Frequency to allow refresh of backstage templates",
            parameter_name=f"/{CmsConstants.STAGE}/common/config/cms-resource-bucket/refresh-frequency-mins",
        )

        aws_ssm.StringParameter(
            self,
            "cms-metrics-reporting-enabled",
            string_value=send_anonymous_usage,
            description="Anonymous metrics reporting enabled state",
            parameter_name=f"/{CmsConstants.STAGE}/common/metrics/enabled",
        )

        metrics_parameter = aws_ssm.StringParameter(
            self,
            "cms-metrics-reporting-url",
            string_value=metrics_url,
            description="Anonymous metrics reporting url",
            parameter_name=f"/{CmsConstants.STAGE}/common/metrics/url",
        )

        metrics_cfn_resource: CfnResource = cast(
            CfnResource, metrics_parameter.node.default_child
        )
        metrics_cfn_resource.cfn_options.condition = send_anonymous_usage_condition
