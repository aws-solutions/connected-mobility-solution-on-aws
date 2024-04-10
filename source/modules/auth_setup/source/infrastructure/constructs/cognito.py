# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# AWS Libraries
from aws_cdk import Aspects, CfnCondition
from constructs import Construct

# CMS Common Library
from cms_common.aspects.condition import ConditionAspect

# Connected Mobility Solution on AWS
from .module_integration import ModuleInputsConstruct
from .services import ServicesConstruct
from .users import UsersConstruct


class CognitoConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        module_inputs_construct: ModuleInputsConstruct,
        should_create_resources_condition: CfnCondition,
    ) -> None:
        super().__init__(scope, construct_id)

        self.users_construct = UsersConstruct(
            self,
            "users",
            module_inputs_construct=module_inputs_construct,
        )

        self.services_construct = ServicesConstruct(
            self,
            "services",
            cognito_id=module_inputs_construct.stack_config.identity_provider_id,
            user_pool=self.users_construct.user_pool,
        )
        Aspects.of(self).add(ConditionAspect(should_create_resources_condition))
