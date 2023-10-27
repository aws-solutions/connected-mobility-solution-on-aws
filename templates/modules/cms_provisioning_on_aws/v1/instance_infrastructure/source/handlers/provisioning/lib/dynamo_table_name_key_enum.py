# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from enum import Enum


class DynamoTableNameKey(Enum):
    AUTHORIZED_VEHICLES_TABLE_NAME = "AUTHORIZED_VEHICLES_TABLE_NAME"
    PROVISIONED_VEHICLES_TABLE_NAME = "PROVISIONED_VEHICLES_TABLE_NAME"
