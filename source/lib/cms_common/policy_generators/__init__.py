# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Connected Mobility Solution on AWS
from .cloudwatch import generate_lambda_cloudwatch_logs_policy_document
from .ec2_vpc import generate_ec2_vpc_policy
from .kms import generate_kms_policy_statement_from_key_id
