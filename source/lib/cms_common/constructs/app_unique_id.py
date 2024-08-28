# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# AWS Libraries
from aws_cdk import CfnParameter, aws_ssm
from constructs import Construct

# Connected Mobility Solution on AWS
from ..config.regex import RegexPattern
from ..config.resource_names import ResourcePrefix, get_application_level_path_prefix
from ..config.ssm import resolve_ssm_parameter


class AppUniqueId:
    @staticmethod
    def create_cfn_parameter(
        scope: Construct,
    ) -> str:
        app_unique_id = CfnParameter(
            scope,
            "AppUniqueId",
            type="String",
            description="Application unique identifier used to uniquely name resources within the stack.",
            allowed_pattern=RegexPattern.APP_UNIQUE_ID,
            constraint_description="AppUniqueId must contain min 3 and max 10 characters, and contain only lowercase alphanumeric characters and dashes.",
            min_length=3,
            max_length=10,
        ).value_as_string

        return app_unique_id

    @staticmethod
    def register(scope: Construct, app_unique_id: str) -> aws_ssm.StringParameter:
        return aws_ssm.StringParameter(
            scope,
            "ssm-app-unique-id",
            parameter_name=f"/{get_application_level_path_prefix(app_unique_id)}",
            string_value=app_unique_id,
            description="SSM parameter to register an app unique ID.",
            simple_name=False,
        )

    @staticmethod
    def register_module(
        scope: Construct, app_unique_id: str, module_name: str
    ) -> aws_ssm.StringParameter:
        return aws_ssm.StringParameter(
            scope,
            "ssm-app-unique-id-register-module",
            parameter_name=ResourcePrefix.slash_separated(
                app_unique_id=app_unique_id,
                module_name=module_name,
                leading_slash=True,
            ),
            string_value=resolve_ssm_parameter(
                parameter_name=get_application_level_path_prefix(
                    app_unique_id, leading_slash=True
                )
            ),
            description="SSM parameter to register a module with an app unique ID.",
            simple_name=False,
        )
