# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# AWS Libraries
from aws_cdk import RemovalPolicy, Stack, aws_kms, aws_timestream
from constructs import Construct

# Connected Mobility Solution on AWS
from .module_integration import TimestreamOutputs


class TimestreamConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        db_name: str,
        table_name: str,
        memory_retention_period_in_hours: str = "24",
        magnetic_retention_period_in_days: str = "14",
    ) -> None:
        super().__init__(scope, construct_id)

        self.timestream_kms_key = aws_kms.Key(
            self,
            "timestream-cmk-key",
            enable_key_rotation=True,
            removal_policy=RemovalPolicy.DESTROY,
        )

        self.timestream_database = aws_timestream.CfnDatabase(
            self,
            "timestream-database",
            database_name=db_name,
            kms_key_id=self.timestream_kms_key.key_id,
        )

        self.timestream_table = aws_timestream.CfnTable(
            self,
            "timestream-table",
            table_name=table_name,
            database_name=self.timestream_database.ref,
            retention_properties={
                "MemoryStoreRetentionPeriodInHours": memory_retention_period_in_hours,
                "MagneticStoreRetentionPeriodInDays": magnetic_retention_period_in_days,
            },
        )

        self.outputs = TimestreamOutputs(
            database_name=self.timestream_database.ref,
            database_arn=self.timestream_database.attr_arn,
            table_name=self.timestream_table.attr_name,
            table_arn=self.timestream_table.attr_arn,
            region=Stack.of(self).region,
            timestream_key_arn=self.timestream_kms_key.key_arn,
        )
