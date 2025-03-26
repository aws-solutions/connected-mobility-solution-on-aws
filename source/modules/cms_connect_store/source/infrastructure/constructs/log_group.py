# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# AWS Libraries
from aws_cdk import aws_logs
from constructs import Construct


class LogGroupConstruct(Construct):
    def __init__(self, scope: Construct, construct_id: str) -> None:
        super().__init__(scope, construct_id)

        self.log_group = aws_logs.LogGroup(
            self,
            "log-group",
            retention=aws_logs.RetentionDays.THREE_MONTHS,
        )
