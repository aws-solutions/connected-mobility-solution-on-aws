# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import re

# Connected Mobility Solution on AWS
from .athena_exceptions import AthenaQueryError


def validate_query_selection_string(value: str) -> None:
    if (
        bool(
            re.match(
                r"^((, )?\"(\w+)\"(\.\"(\w+)\")* as \"(\w+)(\.(\w+))*\")+$", str(value)
            )
        )
        is False
    ):
        raise AthenaQueryError("selection string contained invalid characters")


def validate_query_table_name(value: str) -> None:
    if bool(re.match(r"^[\w-]+$", str(value))) is False:
        raise AthenaQueryError("query table name contained invalid characters")


def validate_query_vin_input(value: str) -> None:
    if bool(re.match(r"^[A-Za-z0-9]+$", str(value))) is False:
        raise AthenaQueryError("vin input contained invalid characters")
