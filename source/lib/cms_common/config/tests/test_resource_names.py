# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Connected Mobility Solution on AWS
from ..resource_names import (
    SOLUTIONS_PREFIX,
    ResourceName,
    ResourcePrefix,
    get_application_level_path_prefix,
    remove_leading_slash,
)


def test_get_application_level_path_prefix_no_leading_slash() -> None:
    assert (
        get_application_level_path_prefix(app_unique_id="test-id") == "solution/test-id"
    )


def test_get_application_level_path_prefix_leading_slash() -> None:
    assert (
        get_application_level_path_prefix(app_unique_id="test-id", leading_slash=True)
        == "/solution/test-id"
    )


def test_remove_leading_slash_with_leading_slash_argument() -> None:
    assert remove_leading_slash("/with/leading/slash") == "with/leading/slash"


def test_remove_leading_slash_without_leading_slash_argument() -> None:
    assert remove_leading_slash("without/leading/slash") == "without/leading/slash"


def test_resource_prefix_slash_separated_leading_slash() -> None:
    assert (
        ResourcePrefix.slash_separated(
            app_unique_id="test-uid", module_name="test-module-name", leading_slash=True
        )
        == f"/{SOLUTIONS_PREFIX}/test-uid/test-module-name"
    )


def test_resource_prefix_slash_separated_no_leading_slash() -> None:
    assert (
        ResourcePrefix.slash_separated(
            app_unique_id="test-uid", module_name="test-module-name"
        )
        == f"{SOLUTIONS_PREFIX}/test-uid/test-module-name"
    )


def test_resource_prefix_hyphen_separated() -> None:
    assert (
        ResourcePrefix.hyphen_separated(
            app_unique_id="test-uid", module_name="test-module-name"
        )
        == "test-uid-test-module-name"
    )


def test_resource_name_slash_separated() -> None:
    assert (
        ResourceName.slash_separated(prefix="test-prefix", name="test-name")
        == "test-prefix/test-name"
    )


def test_resource_name_hyphen_separated() -> None:
    assert (
        ResourceName.hyphen_separated(prefix="test-prefix", name="test-name")
        == "test-prefix-test-name"
    )


def test_resource_name_underscore_separated() -> None:
    assert (
        ResourceName.underscore_separated(prefix="test-prefix", name="test-name")
        == "test-prefix_test-name"
    )
