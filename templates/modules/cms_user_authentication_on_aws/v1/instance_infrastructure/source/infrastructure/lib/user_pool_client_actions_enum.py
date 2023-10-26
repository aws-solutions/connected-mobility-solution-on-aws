# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from enum import Enum


class UserPoolClientActions(Enum):
    CREATE = "CreateUserPoolClient"
    UPDATE = "UpdateUserPoolClient"
    DELETE = "DeleteUserPoolClient"
