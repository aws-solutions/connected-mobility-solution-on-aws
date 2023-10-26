# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any

# Third Party Libraries
from aws_cdk import aws_ssm
from constructs import Construct

# Connected Mobility Solution on AWS
from ...config.constants import AlertsConstants


class ModuleInputsConstruct(Construct):
    def __init__(self, scope: Construct, construct_id: str, **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.token_validation_lambda_arn = aws_ssm.StringParameter.from_string_parameter_attributes(
            self,
            "ssm-token-validation-lambda-arn",
            parameter_name=f"/{AlertsConstants.STAGE}/cms/authentication/token-validation-lambda/arn",
        )


class ModuleOutputsConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        publish_api_endpoint: str,
        frontend_api_endpoint: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        aws_ssm.StringParameter(
            self,
            "alerts-publish-api-endpoint",
            string_value=publish_api_endpoint,
            parameter_name=f"/{AlertsConstants.STAGE}/cms/alerts/publish-api/endpoint",
        )

        aws_ssm.StringParameter(
            self,
            "alerts-frontend-api-endpoint",
            string_value=frontend_api_endpoint,
            parameter_name=f"/{AlertsConstants.STAGE}/cms/alerts/frontend-api/endpoint",
        )
