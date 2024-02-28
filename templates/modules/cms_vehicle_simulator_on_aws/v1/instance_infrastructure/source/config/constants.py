# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
from dataclasses import dataclass


# pylint: disable=invalid-name
@dataclass(frozen=True)
class VSConstantsClass:
    STAGE = os.environ.get("STAGE", "dev")
    APP_NAME = f"cms-vehicle-simulator-on-aws-stack-{STAGE}"
    MODULE_NAME = "cms-vehicle-simulator-on-aws"
    TOPIC_PREFIX = "cms/data/simulated"
    SOLUTION_NAME = "Connected Mobility Solution on AWS"
    SOLUTION_ID = "SO0241"
    SOLUTION_VERSION = "v1.0.4"
    APPLICATION_TYPE = "AWS-Solutions"
    CAPABILITY_ID = "CMS.1"
    USER_AGENT_STRING: str = f"AWSSOLUTION/{SOLUTION_ID}/{SOLUTION_VERSION} AWSSOLUTION-CAPABILITY/{CAPABILITY_ID}/{SOLUTION_VERSION}"


VSConstants = VSConstantsClass()
