# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Connected Mobility Solution on AWS
from ..resource_names.module_short_names import CMSModuleShortNames
from .resource_names import ResourceName, ResourcePrefix


def resolve_ssm_parameter(parameter_name: str) -> str:
    # parameter_name should include any leading slashes that are expected in the ssm parameter name
    return f"{{{{resolve:ssm:{parameter_name}}}}}"


def get_resolvable_ssm_deployment_uuid(app_unique_id: str) -> str:
    deployment_uuid_ssm_parameter_name = ResourceName.slash_separated(
        prefix=ResourcePrefix.slash_separated(
            app_unique_id=app_unique_id,
            module_name=CMSModuleShortNames.CONFIG,
            leading_slash=True,
        ),
        name="deployment-uuid",
    )
    return resolve_ssm_parameter(deployment_uuid_ssm_parameter_name)


def get_resolvable_ssm_metrics_url(app_unique_id: str) -> str:
    metrics_url_ssm_parameter_name = ResourceName.slash_separated(
        prefix=ResourcePrefix.slash_separated(
            app_unique_id=app_unique_id,
            module_name=CMSModuleShortNames.CONFIG,
            leading_slash=True,
        ),
        name="metrics/url",
    )
    return resolve_ssm_parameter(metrics_url_ssm_parameter_name)


def get_resolvable_ssm_metrics_enabled(app_unique_id: str) -> str:
    metrics_enabled_ssm_parameter_name = ResourceName.slash_separated(
        prefix=ResourcePrefix.slash_separated(
            app_unique_id=app_unique_id,
            module_name=CMSModuleShortNames.CONFIG,
            leading_slash=True,
        ),
        name="metrics/enabled",
    )
    return resolve_ssm_parameter(metrics_enabled_ssm_parameter_name)
