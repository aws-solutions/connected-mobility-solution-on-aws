# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import dataclasses

# Third Party Libraries
from dataclass_type_validator import dataclass_validate  # type: ignore

# AWS Libraries
from aws_cdk import aws_dynamodb, aws_kms
from constructs import Construct


@dataclass_validate
@dataclasses.dataclass(frozen=True)
class ProvisioningDBResources:
    authorized_vehicles_table_kms_key: aws_kms.Key
    authorized_vehicles_table: aws_dynamodb.Table
    provisioned_vehicles_table_kms_key: aws_kms.Key
    provisioned_vehicles_table: aws_dynamodb.Table


class ProvisioningDatabaseConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
    ) -> None:
        super().__init__(scope, construct_id)

        authorized_vehicles_table_kms_key = aws_kms.Key(
            self,
            "authorized-vehicles-table-kms-key",
            enable_key_rotation=True,
        )
        authorized_vehicles_table = aws_dynamodb.Table(
            self,
            "authorized-vehicles-table",
            partition_key=aws_dynamodb.Attribute(
                name="vin",
                type=aws_dynamodb.AttributeType.STRING,
            ),
            billing_mode=aws_dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption_key=authorized_vehicles_table_kms_key,
            point_in_time_recovery=True,
        )

        provisioned_vehicles_table_kms_key = aws_kms.Key(
            self,
            "provisioned-vehicles-table-kms-key",
            enable_key_rotation=True,
        )
        provisioned_vehicles_table = aws_dynamodb.Table(
            self,
            "provisioned-vehicles-table",
            partition_key=aws_dynamodb.Attribute(
                name="vin",
                type=aws_dynamodb.AttributeType.STRING,
            ),
            sort_key=aws_dynamodb.Attribute(
                name="certificate_id",
                type=aws_dynamodb.AttributeType.STRING,
            ),
            billing_mode=aws_dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption_key=provisioned_vehicles_table_kms_key,
            point_in_time_recovery=True,
        )

        self.db_resources = ProvisioningDBResources(
            authorized_vehicles_table_kms_key=authorized_vehicles_table_kms_key,
            authorized_vehicles_table=authorized_vehicles_table,
            provisioned_vehicles_table_kms_key=provisioned_vehicles_table_kms_key,
            provisioned_vehicles_table=provisioned_vehicles_table,
        )
