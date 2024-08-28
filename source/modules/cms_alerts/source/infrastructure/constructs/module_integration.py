# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any

# AWS Libraries
from aws_cdk import CfnParameter, Stack, aws_ssm
from constructs import Construct

# CMS Common Library
from cms_common.config.resource_names import ResourceName, ResourcePrefix
from cms_common.config.ssm import resolve_ssm_parameter
from cms_common.config.stack_inputs import SolutionConfigInputs
from cms_common.constructs.app_unique_id import AppUniqueId
from cms_common.constructs.vpc_construct import create_vpc_config, get_vpc_name
from cms_common.resource_names.module_short_names import CMSModuleShortNames


class ModuleInputsConstruct(Construct):
    def __init__(self, scope: Construct, construct_id: str, **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.app_unique_id = AppUniqueId.create_cfn_parameter(Stack.of(self))

        self.sns_topic_prefix = CfnParameter(
            Stack.of(self),
            "SnsTopicPrefix",
            type="String",
            description="SNS topic name prefix for topics created by alerts module.",
            min_length=3,
            constraint_description="Topic name prefix should contain a minimum of 3 characters.",
            default="CMS",
        ).value_as_string

        self.vpc_config = create_vpc_config(
            vpc_name=get_vpc_name(self, app_unique_id=self.app_unique_id)
        )

        auth_module_ssm_prefix_with_leading_slash = ResourcePrefix.slash_separated(
            app_unique_id=self.app_unique_id,
            module_name=CMSModuleShortNames.AUTH,
            leading_slash=True,
        )
        self.token_validation_lambda_arn = resolve_ssm_parameter(
            parameter_name=ResourceName.slash_separated(
                prefix=auth_module_ssm_prefix_with_leading_slash,
                name="token-validation-lambda/arn",
            )
        )


class ModuleOutputsConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_unique_id: str,
        solution_config_inputs: SolutionConfigInputs,
        publish_api_endpoint: str,
        frontend_api_endpoint: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        ssm_parameter_name_prefix = ResourcePrefix.slash_separated(
            app_unique_id=app_unique_id,
            module_name=solution_config_inputs.module_short_name,
            leading_slash=True,
        )

        aws_ssm.StringParameter(
            self,
            "alerts-publish-api-endpoint",
            string_value=publish_api_endpoint,
            parameter_name=ResourceName.slash_separated(
                prefix=ssm_parameter_name_prefix, name="publish-api/endpoint"
            ),
            simple_name=False,
        )

        aws_ssm.StringParameter(
            self,
            "alerts-frontend-api-endpoint",
            string_value=frontend_api_endpoint,
            parameter_name=ResourceName.slash_separated(
                prefix=ssm_parameter_name_prefix, name="frontend-api/endpoint"
            ),
            simple_name=False,
        )
