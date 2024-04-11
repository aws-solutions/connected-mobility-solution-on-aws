# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0


def resolve_ssm_parameter(parameter_name: str) -> str:
    # parameter_name should have any leading slashes expected in the ssm parameter name
    return f"{{{{resolve:ssm:{parameter_name}}}}}"
