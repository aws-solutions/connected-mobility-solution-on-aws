# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from dataclasses import dataclass

# Connected Mobility Solution on AWS
from .module_short_names import CMSModuleShortNames


@dataclass(frozen=True)
class ConfigResourceNames:
    config_prefix: str
    aws_resource_lookup_lambda_arn_ssm_parameter: str
    identity_provider_id_ssm_parameter: str
    vpc_name_ssm_parameter: str

    @classmethod
    def from_app_unique_id(cls, app_unique_id: str) -> "ConfigResourceNames":
        config_prefix = f"/solution/{app_unique_id}/{CMSModuleShortNames.CONFIG}"
        return ConfigResourceNames(
            config_prefix=config_prefix,
            identity_provider_id_ssm_parameter=f"{config_prefix}/auth/identity-provider-id",
            aws_resource_lookup_lambda_arn_ssm_parameter=f"{config_prefix}/aws-resource-lookup-lambda/arn",
            vpc_name_ssm_parameter=f"{config_prefix}/vpc/name",
        )
