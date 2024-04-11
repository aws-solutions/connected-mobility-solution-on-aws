# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
# AWS Libraries
from aws_cdk import Fn

SOLUTIONS_PREFIX = "solution"

# NOTE: These functions must use Cfn functions for string manipulation since AppUniqueId can be a token and therefore not resolvable yet in the template.
# This is not necessary for basic string concatenation or f strings as Cloud Formation handles this automatically.


def get_application_level_path_prefix(
    app_unique_id: str, leading_slash: bool = False
) -> str:
    path_prefix = f"{SOLUTIONS_PREFIX}/{app_unique_id}"
    return f"/{path_prefix}" if leading_slash else path_prefix


class ResourcePrefix:
    @staticmethod
    def slash_separated(
        app_unique_id: str, module_name: str, leading_slash: bool = False
    ) -> str:
        return f"{get_application_level_path_prefix(app_unique_id=app_unique_id, leading_slash=leading_slash)}/{module_name}"

    @staticmethod
    def hyphen_separated(app_unique_id: str, module_name: str) -> str:
        return f"{app_unique_id}-{module_name}"

    @staticmethod
    def only_underscore_separated(app_unique_id: str, module_name: str) -> str:
        prefix = f"{app_unique_id}_{module_name}"
        return Fn.join("_", Fn.split("-", prefix))


class ResourceName:
    @staticmethod
    def slash_separated(prefix: str, name: str) -> str:
        return f"{prefix}/{name}"

    @staticmethod
    def hyphen_separated(prefix: str, name: str) -> str:
        return f"{prefix}-{name}"

    @staticmethod
    def underscore_separated(prefix: str, name: str) -> str:
        return f"{prefix}_{name}"
