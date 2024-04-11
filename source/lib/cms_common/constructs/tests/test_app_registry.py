# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
from syrupy.types import SerializableData

# AWS Libraries
from aws_cdk import Stack, assertions

# Connected Mobility Solution on AWS
from ..app_registry import AppRegistryConstruct, AppRegistryInputs


def test_app_registry_snapshot(
    snapshot_json_with_matcher: SerializableData,
) -> None:
    stack = Stack()
    AppRegistryConstruct(
        stack,
        "test-app-registry",
        app_registry_inputs=AppRegistryInputs(
            application_name="test-application-name",
            application_type="test-application-type",
            solution_id="test-solution-id",
            solution_name="test-solution-name",
            solution_version="test-solution-version",
        ),
    )
    assert assertions.Template.from_stack(stack).to_json() == snapshot_json_with_matcher
