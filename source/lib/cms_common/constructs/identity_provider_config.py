# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# AWS Libraries
from aws_cdk import CfnParameter, CustomResource
from constructs import Construct

# Connected Mobility Solution on AWS
from ..config.ssm import resolve_ssm_parameter
from ..enums.aws_resource_lookup import AwsResourceLookupCustomResourceType
from ..resource_names.config import ConfigResourceNames


class IdentityProviderConfig:
    @staticmethod
    def create_cfn_parameter(
        scope: Construct,
    ) -> str:
        identity_provider_id = CfnParameter(
            scope,
            "IdentityProviderId",
            type="String",
            description="The ID associated with the identity provider configurations used for validation and exchange.",
            min_length=3,
            constraint_description=(
                "The identity provider ID must be a minimum of 3 characters."
            ),
            default="cms",
        ).value_as_string

        return identity_provider_id

    @staticmethod
    def get_identity_provider_id(scope: Construct, app_unique_id: str) -> str:
        config_resource_names = ConfigResourceNames.from_app_unique_id(app_unique_id)

        aws_resource_lookup_lambda_arn = resolve_ssm_parameter(
            parameter_name=config_resource_names.aws_resource_lookup_lambda_arn_ssm_parameter
        )

        identity_provider_id_custom_resource = CustomResource(
            scope,
            "identity-provider-id-custom-resource",
            service_token=aws_resource_lookup_lambda_arn,
            resource_type=f"Custom::{AwsResourceLookupCustomResourceType.SSM_PARAMETERS.value}",
            properties={
                "Resource": AwsResourceLookupCustomResourceType.SSM_PARAMETERS.value,
                "ParameterName": config_resource_names.identity_provider_id_ssm_parameter,
            },
        )

        return identity_provider_id_custom_resource.get_att_string("parameter_value")
