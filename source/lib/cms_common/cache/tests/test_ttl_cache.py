# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from time import sleep

# Connected Mobility Solution on AWS
from ..ttl_cache import get_ttl_cache_check


def test_get_ttl_cache_check_hit() -> None:
    ttl_cache_check_one = get_ttl_cache_check(ttl_in_seconds=5)
    ttl_cache_check_two = get_ttl_cache_check(ttl_in_seconds=5)
    assert ttl_cache_check_two - ttl_cache_check_one == 0


def test_get_ttl_cache_check_miss() -> None:
    ttl_cache_check_one = get_ttl_cache_check(ttl_in_seconds=2)
    sleep(2)
    ttl_cache_check_two = get_ttl_cache_check(ttl_in_seconds=2)
    assert ttl_cache_check_two - ttl_cache_check_one == 1
