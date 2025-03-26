# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0


class MultiAccountConfig:
    AVAILABLE_REGIONS_SSM_PARAMETER_NAME = (
        "/solution/acdp/multi-acct-setup/available-regions"
    )
    ENROLLED_ORGS_SSM_PARAMETER_NAME = (
        "/solution/acdp/multi-acct-setup/enrolled-organizations"
    )
    ORGS_ACCOUNT_DIRECTORY_ASSUME_ROLE_NAME = "acdp-orgs-trust-role"
    DEPLOYMENT_ROLE_NAME = "acdp-codebuild-assume-role"
    CLOUDFORMATION_ROLE_NAME = "acdp-cloudformation-role"
    METRICS_ROLE_NAME = "acdp-metrics-role"
