# -*- coding: utf-8 -*-

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
from dataclasses import dataclass


# pylint: disable=invalid-name
@dataclass(frozen=True)
class BackstageConstantsClass:
    AWS_ACCOUNT_ID: str = os.environ.get("AWS_ACCOUNT_ID", "test")
    REGION: str = os.environ.get("AWS_REGION", "us-west-2")
    STAGE: str = os.environ.get("STAGE", "dev")
    APP_NAME: str = "cms-backstage"
    STACK_NAME: str = f"cms-backstage-{STAGE}"
    ENV_APP_NAME: str = f"cms-backstage-env-{STAGE}"
    MODULE_NAME: str = f"Cms-backstage-on-aws-{STAGE}"
    SOLUTION_NAME: str = "Connected Mobility Solution on AWS"
    APPLICATION_TYPE: str = "AWS-Solutions"
    SOLUTION_ID: str = "SO0241"
    SOLUTION_VERSION: str = "v1.0.2"
    CAPABILITY_ID = "CMS.6"
    USER_AGENT_STRING: str = f"AWSSOLUTION/{SOLUTION_ID}/{SOLUTION_VERSION} AWSSOLUTION-CAPABILITY/{CAPABILITY_ID}/{SOLUTION_VERSION}"


BackstageConstants = BackstageConstantsClass()
