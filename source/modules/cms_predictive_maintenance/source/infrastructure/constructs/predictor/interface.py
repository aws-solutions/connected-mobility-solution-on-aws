# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import dataclasses


@dataclasses.dataclass(frozen=True)
class PredictorConstructOutputs:
    pipeline_role_arn: str
    pipeline_assets_bucket_name: str
    deploy_model_lambda_function_arn: str
    deploy_model_endpoint_name: str
