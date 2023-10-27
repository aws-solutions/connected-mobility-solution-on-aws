# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
import pytest
from syrupy.extensions.json import JSONSnapshotExtension
from syrupy.matchers import path_type
from syrupy.types import SerializableData


@pytest.fixture(name="snapshot_json_with_matcher")
def fixture_snapshot_json_with_matcher(snapshot: SerializableData) -> SerializableData:
    matcher = path_type(
        mapping={"^(.*)\\.S3Key$": (str,), "^(.*)\\.TemplateURL\\.(.*)$": (list,)},
        regex=True,
    )
    return snapshot.use_extension(JSONSnapshotExtension)(matcher=matcher)
