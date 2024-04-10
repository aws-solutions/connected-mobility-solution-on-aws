# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from enum import Enum


class AwsResourceLookupCustomResourceType(Enum):
    SSM_PARAMETERS = "SsmParameters"
