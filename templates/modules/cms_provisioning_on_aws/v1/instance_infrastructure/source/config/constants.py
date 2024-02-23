# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
from dataclasses import dataclass


# pylint: disable=invalid-name
@dataclass(frozen=True)
class VPConstantsClass:
    STAGE = os.environ.get("STAGE", "dev")
    APP_NAME = f"cms-provisioning-on-aws-stack-{STAGE}"
    MODULE_NAME = "cms-provisioning-on-aws"
    SOLUTION_NAME = "Connected Mobility Solution on AWS"
    PROVISIONING_TEMPLATE_NAME = "cms-vehicle-provisioning-template"
    CLAIM_CERT_PROVISIONING_POLICY_NAME = "claim-certificate-provisioning-policy"
    SOLUTION_ID = "SO0241"
    SOLUTION_VERSION = "v1.0.3"
    APPLICATION_TYPE = "AWS-Solutions"
    CAPABILITY_ID = "CMS.5"
    USER_AGENT_STRING: str = (
        f"AWSSOLUTION/{SOLUTION_ID}/{SOLUTION_VERSION} AWSSOLUTION-CAPABILITY/{CAPABILITY_ID}/{SOLUTION_VERSION}"
    )


VPConstants = VPConstantsClass()
