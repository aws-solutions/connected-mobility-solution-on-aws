# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
from dataclasses import dataclass


# pylint: disable=invalid-name
@dataclass(frozen=True)
class ConnectStoreConstantsClass:
    STAGE: str = os.environ.get("STAGE", "dev")
    APP_NAME: str = f"cms-connect-store-on-aws-stack-{STAGE}"
    MODULE_NAME: str = "cms-connect-store-on-aws"
    SOLUTION_NAME: str = "Connected Mobility Solution on AWS"
    SOLUTION_ID: str = "SO0241"
    SOLUTION_VERSION: str = "v1.0.4"
    APPLICATION_TYPE: str = "AWS-Solutions"
    CAPABILITY_ID = "CMS.3"
    USER_AGENT_STRING: str = f"AWSSOLUTION/{SOLUTION_ID}/{SOLUTION_VERSION} AWSSOLUTION-CAPABILITY/{CAPABILITY_ID}/{SOLUTION_VERSION}"


ConnectStoreConstants = ConnectStoreConstantsClass()
