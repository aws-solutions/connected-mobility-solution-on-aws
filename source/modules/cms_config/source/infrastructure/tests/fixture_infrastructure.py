# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
import pytest
from syrupy.extensions.json import JSONSnapshotExtension
from syrupy.matchers import path_value
from syrupy.types import SerializableData


@pytest.fixture(name="snapshot_json_with_matcher")
def fixture_snapshot_json_with_matcher(snapshot: SerializableData) -> SerializableData:
    matcher = path_value(
        mapping={
            ".*": r"(\/?([0-9a-fA-F]+)\.zip|[a-zA-Z0-9:/-]+([0-9]{12})[a-zA-Z0-9:/-]+)",
        },
        regex=True,
        types=(object,),
        replacer=lambda data, match: data.replace(match[1], "test") if match else data,
    )
    return snapshot.use_extension(JSONSnapshotExtension)(matcher=matcher)
