# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library

# AWS Libraries
from aws_cdk import CfnCondition, Fn, aws_cognito
from constructs import Construct

# Connected Mobility Solution on AWS
from ..constructs.module_integration import ModuleInputsConstruct


class CognitoUserConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        module_inputs: ModuleInputsConstruct,
    ) -> None:
        super().__init__(scope, construct_id)

        cognito_admin_user_pool_user = aws_cognito.CfnUserPoolUser(
            self,
            "admin-user",
            user_pool_id=module_inputs.user_pool_id,
            username=module_inputs.admin_username,
            desired_delivery_mediums=["EMAIL"],
            force_alias_creation=True,
            user_attributes=[
                {"name": "email", "value": module_inputs.admin_user_email},
                {"name": "email_verified", "value": "True"},
            ],
        )

        cognito_admin_user_pool_user.cfn_options.condition = CfnCondition(
            self,
            "should-create-cognito-admin-user-condition",
            expression=Fn.condition_equals(
                module_inputs.should_create_cognito_user,
                "true",
            ),
        )
