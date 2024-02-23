# -*- coding: utf-8 -*-

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
from dataclasses import dataclass


# pylint: disable=invalid-name
@dataclass(frozen=True)
class UserAuthenticationConstantsClass:
    STAGE: str = os.environ.get("STAGE", "dev")
    APP_NAME: str = f"cms-user-authentication-on-aws-stack-{STAGE}"
    MODULE_NAME: str = "cms-user-authentication-on-aws"
    SOLUTION_NAME: str = "Connected Mobility Solution on AWS"
    SOLUTION_ID: str = "SO0241"
    SOLUTION_VERSION: str = "v1.0.3"
    APPLICATION_TYPE: str = "AWS-Solutions"
    CAPABILITY_ID = "CMS.22"
    USER_AGENT_STRING: str = f"AWSSOLUTION/{SOLUTION_ID}/{SOLUTION_VERSION} AWSSOLUTION-CAPABILITY/{CAPABILITY_ID}/{SOLUTION_VERSION}"


UserAuthenticationConstants = UserAuthenticationConstantsClass()
