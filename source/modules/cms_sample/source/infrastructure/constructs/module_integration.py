# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
# AWS Libraries
from aws_cdk import Stack
from constructs import Construct

# CMS Common Library
from cms_common.constructs.app_unique_id import AppUniqueId


class ModuleInputsConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
    ) -> None:
        super().__init__(scope, construct_id)

        self.app_unique_id = AppUniqueId.create_cfn_parameter(Stack.of(self))
