# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

# Standard Library
from typing import TYPE_CHECKING

# Third Party Libraries
from aws_cdk import CfnMapping, Fn, Stack, aws_ssm
from constructs import Construct

# Connected Mobility Solution on AWS
from ...config.constants import VSConstants

if TYPE_CHECKING:
    # Connected Mobility Solution on AWS
    from ..cms_vehicle_simulator_on_aws_stack import InfrastructureGeneralStack


class StackConfig(Construct):
    solution_id = None
    solution_version = None
    solution_mapping = None

    def __init__(self, scope: InfrastructureGeneralStack, stack_id: str):
        super().__init__(scope, stack_id)

        self.solution_mapping = CfnMapping(
            scope,
            "solution",
            mapping={
                "Config": {
                    "SolutionId": "SO0041",
                    "Version": "VERSION_PLACEHOLDER",
                    "SendAnonymousUsage": "Yes",
                    "S3Bucket": "BUCKET_NAME_PLACEHOLDER",
                    "KeyPrefix": "SOLUTION_NAME_PLACEHOLDER/VERSION_PLACEHOLDER",
                }
            },
            lazy=True,
        )
        self.solution_id = self.solution_mapping.find_in_map("Config", "SolutionId")
        self.solution_version = self.solution_mapping.find_in_map("Config", "Version")

        scope.export_value(
            self.solution_mapping.find_in_map("Config", "SendAnonymousUsage"),
            name=f"{VSConstants.APP_NAME}-send-anonymous-usage",
        )
        scope.export_value(
            self.solution_version, name=f"{VSConstants.APP_NAME}-solution-version"
        )
        scope.export_value(
            Fn.join(
                "-",
                [
                    self.solution_mapping.find_in_map("Config", "S3Bucket"),
                    Stack.of(self).region,
                ],
            ),
            name=f"{VSConstants.APP_NAME}-source-code-bucket-name",
        )
        scope.export_value(
            self.solution_mapping.find_in_map("Config", "KeyPrefix"),
            name=f"{VSConstants.APP_NAME}-source-code-prefix",
        )

        aws_ssm.StringParameter(
            self,
            "ssm-solution-id",
            string_value=self.solution_id,
            description="ID for this solution",
            parameter_name=f"/{VSConstants.STAGE}/{VSConstants.APP_NAME}/solution/id",
        )
