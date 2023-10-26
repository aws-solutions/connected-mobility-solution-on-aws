# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

# Standard Library
from typing import TYPE_CHECKING

# Third Party Libraries
from aws_cdk import aws_dynamodb, aws_ssm
from constructs import Construct

# Connected Mobility Solution on AWS
from ...config.constants import VSConstants

if TYPE_CHECKING:
    # Connected Mobility Solution on AWS
    from ..cms_vehicle_simulator_on_aws_stack import InfrastructureGeneralStack


class StorageConstruct(Construct):
    def __init__(self, scope: InfrastructureGeneralStack, stack_id: str) -> None:
        super().__init__(scope, stack_id)

        self.simulations_table = aws_dynamodb.Table(
            self,
            "vs-simulations-table",
            billing_mode=aws_dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=aws_dynamodb.TableEncryption.AWS_MANAGED,
            partition_key={"name": "sim_id", "type": aws_dynamodb.AttributeType.STRING},
            point_in_time_recovery=True,
        )

        self.devices_types_table = aws_dynamodb.Table(
            self,
            "vs-device-types-table",
            billing_mode=aws_dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=aws_dynamodb.TableEncryption.AWS_MANAGED,
            partition_key={
                "name": "type_id",
                "type": aws_dynamodb.AttributeType.STRING,
            },
            point_in_time_recovery=True,
        )

        self.templates_table = aws_dynamodb.Table(
            self,
            "vs-templates-table",
            billing_mode=aws_dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=aws_dynamodb.TableEncryption.AWS_MANAGED,
            partition_key={
                "name": "template_id",
                "type": aws_dynamodb.AttributeType.STRING,
            },
            point_in_time_recovery=True,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-simulations-table-arn",
            string_value=self.simulations_table.table_arn,
            description="Simulations table arn",
            parameter_name=f"/{VSConstants.STAGE}/{VSConstants.APP_NAME}/dynamodb/simulations-table-arn",
        )
        aws_ssm.StringParameter(
            self,
            "ssm-devices-types-table-arn",
            string_value=self.devices_types_table.table_arn,
            description="Devices table arn",
            parameter_name=f"/{VSConstants.STAGE}/{VSConstants.APP_NAME}/dynamodb/devices-types-table-arn",
        )
        aws_ssm.StringParameter(
            self,
            "ssm-simulations-table-name",
            string_value=self.simulations_table.table_name,
            description="Simulations table name",
            parameter_name=f"/{VSConstants.STAGE}/{VSConstants.APP_NAME}/dynamodb/simulations-table-name",
        )
        aws_ssm.StringParameter(
            self,
            "ssm-devices-types-table-name",
            string_value=self.devices_types_table.table_name,
            description="Devices table name",
            parameter_name=f"/{VSConstants.STAGE}/{VSConstants.APP_NAME}/dynamodb/devices-types-table-name",
        )
        aws_ssm.StringParameter(
            self,
            "ssm-templates-table-arn",
            string_value=self.templates_table.table_arn,
            description="Templates table arn",
            parameter_name=f"/{VSConstants.STAGE}/{VSConstants.APP_NAME}/dynamodb/templates-table-arn",
        )
        aws_ssm.StringParameter(
            self,
            "ssm-templates-table-name",
            string_value=self.templates_table.table_name,
            description="Templates table name",
            parameter_name=f"/{VSConstants.STAGE}/{VSConstants.APP_NAME}/dynamodb/templates-table-name",
        )
