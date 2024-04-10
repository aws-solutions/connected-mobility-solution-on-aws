# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

# AWS Libraries
from aws_cdk import aws_dynamodb
from constructs import Construct


class StorageConstruct(Construct):
    def __init__(self, scope: Construct, stack_id: str) -> None:
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
