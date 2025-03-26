# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from enum import Enum


class CustomResourceFunctionType(Enum):
    SEND_ANONYMOUS_METRICS = "SendAnonymousMetrics"
    CREATE_CONFIG = "CreateConfig"
    CREATE_USERPOOL_USER = "CreateUserpoolUser"
