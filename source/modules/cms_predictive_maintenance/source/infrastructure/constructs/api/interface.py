# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from dataclasses import dataclass


@dataclass(frozen=True)
class BatchInferenceConfig:
    data_s3_key_prefix: str
    instance_type: str
    instance_count: int


@dataclass(frozen=True)
class PredictApiOutputs:
    endpoint_url: str
