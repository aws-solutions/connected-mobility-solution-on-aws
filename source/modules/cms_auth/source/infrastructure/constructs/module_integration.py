# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# AWS Libraries
from aws_cdk import Stack, aws_ssm
from constructs import Construct

# CMS Common Library
from cms_common.constructs.app_unique_id import AppUniqueId
from cms_common.constructs.identity_provider_config import IdentityProviderConfig
from cms_common.constructs.vpc_construct import create_vpc_config, get_vpc_name
from cms_common.resource_names.auth import AuthResourceNames


class ModuleInputsConstruct(Construct):
    def __init__(self, scope: Construct, construct_id: str) -> None:
        super().__init__(scope, construct_id)

        self.app_unique_id = AppUniqueId.create_cfn_parameter(Stack.of(self))

        self.identity_provider_id = IdentityProviderConfig.get_identity_provider_id(
            scope=self, app_unique_id=self.app_unique_id
        )

        self.vpc_config = create_vpc_config(
            vpc_name=get_vpc_name(scope=self, app_unique_id=self.app_unique_id)
        )


class ModuleOutputsConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_unique_id: str,
        authorization_code_exchange_lambda_arn: str,
        token_validation_lambda_arn: str,
    ) -> None:
        super().__init__(scope, construct_id)

        auth_resource_names = AuthResourceNames.from_app_unique_id(
            app_unique_id=app_unique_id
        )

        aws_ssm.StringParameter(
            self,
            "ssm-authorization-code-exchange-lambda-arn",
            string_value=authorization_code_exchange_lambda_arn,
            description="Arn for lambda function that facilitates the exchange an authorization code for user tokens via the authorization code flow.",
            parameter_name=auth_resource_names.authorization_code_exchange_lambda_arn,
            simple_name=False,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-token-validation-lambda-arn",
            string_value=token_validation_lambda_arn,
            description="Arn for lambda function that verifies the validity and claims of auth tokens.",
            parameter_name=auth_resource_names.token_validation_lambda_arn,
            simple_name=False,
        )
