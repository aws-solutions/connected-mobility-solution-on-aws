# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Connected Mobility Solution on AWS
from .condition import ConditionAspect
from .nag_suppression import NagSuppression, NagType
from .vpc_aspect import (
    ApplyVpcOnCustomResource,
    generate_ec2_vpc_policy_cfn_format,
    make_vpc_cfn_config,
)
