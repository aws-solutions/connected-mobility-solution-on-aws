# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from enum import Enum


class NagType(Enum):
    CDK_NAG = "cdk_nag"
    CFN_NAG = "cfn_nag"
