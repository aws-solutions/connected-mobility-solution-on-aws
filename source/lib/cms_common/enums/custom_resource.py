# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from enum import Enum


class CustomResourceRequestType(Enum):
    CREATE = "Create"
    UPDATE = "Update"
    DELETE = "Delete"


class CustomResourceStatusType(Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
