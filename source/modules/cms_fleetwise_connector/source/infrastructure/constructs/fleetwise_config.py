# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# IMPLEMENT: Insert IAM roles/policies required by FW to connect to Timestream
# SEE: https://docs.aws.amazon.com/iot-fleetwise/latest/developerguide/controlling-access.html

# AWS Libraries
from aws_cdk import Stack, aws_iam
from constructs import Construct

# CMS Common Library
from cms_common.config.resource_names import ResourceName, ResourcePrefix
from cms_common.config.stack_inputs import SolutionConfigInputs


class FleetWiseConfigConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_unique_id: str,
        solution_config_inputs: SolutionConfigInputs,
        timestream_table_arn: str,
        timestream_kms_key_arn: str,
    ) -> None:
        super().__init__(scope, construct_id)

        self.fleetwise_execution_role = aws_iam.Role(
            self,
            "fleetwise-execution-role",
            role_name=ResourceName.hyphen_separated(
                prefix=ResourcePrefix.hyphen_separated(
                    app_unique_id=app_unique_id,
                    module_name=solution_config_inputs.module_short_name,
                ),
                name=f"{Stack.of(self).region}-fw-execution-role",
            ),
            assumed_by=aws_iam.ServicePrincipal("iotfleetwise.amazonaws.com"),
            inline_policies={
                "timestream-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "timestream:WriteRecords",
                                "timestream:Select",
                            ],
                            resources=[timestream_table_arn],
                        ),
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "timestream:DescribeEndpoints",
                            ],
                            resources=["*"],
                        ),
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "kms:GenerateDataKey",
                                "kms:Decrypt",
                                "kms:Encrypt",
                            ],
                            resources=[timestream_kms_key_arn],
                        ),
                    ]
                ),
            },
        )
