# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library

# Standard Library
from typing import List

# Third Party Libraries
from aws_cdk import aws_grafana, aws_iam
from constructs import Construct

# Connected Mobility Solution on AWS
from ...config.constants import EVBatteryHealthConstants


class GrafanaWorkspaceConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        data_sources: List[str],
        notification_destinations: List[str],
    ) -> None:
        super().__init__(scope, construct_id)

        self.workspace_role = aws_iam.Role(
            self,
            "workspace-role",
            assumed_by=aws_iam.ServicePrincipal("grafana.amazonaws.com"),
            inline_policies={},
        )

        self.workspace = aws_grafana.CfnWorkspace(
            self,
            "workspace",
            account_access_type="CURRENT_ACCOUNT",
            authentication_providers=["AWS_SSO"],
            permission_type="CUSTOMER_MANAGED",
            description="Grafana workspace for EV Battery Health Monitoring.",
            grafana_version="9.4",
            name=f"ev-battery-health-grafana-workspace-{EVBatteryHealthConstants.STAGE}",
            notification_destinations=notification_destinations,
            data_sources=data_sources,
            role_arn=self.workspace_role.role_arn,
            plugin_admin_enabled=True,
        )

    def add_policy_to_grafana_workspace(self, policy: aws_iam.Policy) -> None:
        self.workspace_role.attach_inline_policy(policy)
