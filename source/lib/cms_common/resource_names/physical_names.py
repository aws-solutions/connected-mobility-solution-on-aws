# -*- coding: utf-8 -*-

# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import List

# AWS Libraries
from aws_cdk import Fn, Stack
from constructs import Construct

GUID_LENGTH = 36

# Generates a physical id, shorter than max_length, with an appended unique stack identifier. Format: <prefix><all_substrings>-<stack_id_guid>
def generate_physical_name(
    scope: Construct,
    prefix: str,
    physical_name_substrings: List[str],
    max_length: int,
) -> str:
    prefix_length = len(prefix)
    max_parts_length = (
        max_length - prefix_length - 1 - GUID_LENGTH
    )  # 1 is for the hyphen, GUID_LENGTH is for the GUID fetched from the stack_id for this scope's stack

    unique_stack_id_part = Fn.select(2, Fn.split("/", Stack.of(scope).stack_id))

    all_substrings = "".join(physical_name_substrings)

    if len(all_substrings) > max_parts_length:
        substring_length = max_parts_length // 2
        all_substrings = (
            all_substrings[:substring_length]
            + all_substrings[len(all_substrings) - substring_length :]
        )

    return prefix.lower() + all_substrings + "-" + unique_stack_id_part
