# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import time

TEN_MINUTES_IN_SECONDS = 600


def get_ttl_cache_check(ttl_in_seconds: int = TEN_MINUTES_IN_SECONDS) -> int:
    return round(time.time() / ttl_in_seconds)
