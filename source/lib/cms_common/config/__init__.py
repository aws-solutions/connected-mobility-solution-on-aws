# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Connected Mobility Solution on AWS
from .metrics import OperationalMetricsInput
from .multi_account import MultiAccountConfig
from .resource_names import (
    ResourceName,
    ResourcePrefix,
    get_application_level_path_prefix,
    remove_leading_slash,
)
from .ssm import (
    get_resolvable_ssm_deployment_uuid,
    get_resolvable_ssm_metrics_enabled,
    get_resolvable_ssm_metrics_url,
    resolve_ssm_parameter,
)
from .stack_inputs import (
    S3AssetConfigInputs,
    SolutionConfigInputs,
    create_solution_tags_for_stack,
    create_stack_description,
)
