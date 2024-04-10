# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0


# Standard Library
from typing import List

# AWS Libraries
from aws_cdk import aws_ec2, aws_grafana, aws_iam
from constructs import Construct

# CMS Common Library
from cms_common.config.resource_names import ResourceName, ResourcePrefix
from cms_common.config.stack_inputs import SolutionConfigInputs
from cms_common.constructs.vpc_construct import VpcConstruct


class GrafanaWorkspaceConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_unique_id: str,
        data_sources: List[str],
        notification_destinations: List[str],
        vpc_construct: VpcConstruct,
        solution_config_inputs: SolutionConfigInputs,
    ) -> None:
        super().__init__(scope, construct_id)

        self.workspace_role = aws_iam.Role(
            self,
            "workspace-role",
            assumed_by=aws_iam.ServicePrincipal("grafana.amazonaws.com"),
            inline_policies={},
        )

        security_group = aws_ec2.SecurityGroup(
            self,
            "security-group",
            vpc=vpc_construct.vpc,
            allow_all_outbound=True,  # NOSONAR
        )

        self.workspace = aws_grafana.CfnWorkspace(
            self,
            "workspace",
            account_access_type="CURRENT_ACCOUNT",
            authentication_providers=["AWS_SSO"],
            permission_type="CUSTOMER_MANAGED",
            description="Grafana workspace for EV Battery Health Monitoring.",
            grafana_version="9.4",
            name=ResourceName.hyphen_separated(
                prefix=ResourcePrefix.hyphen_separated(
                    app_unique_id=app_unique_id,
                    module_name=solution_config_inputs.module_short_name,
                ),
                name="dashboard-and-alerts",
            ),
            notification_destinations=notification_destinations,
            data_sources=data_sources,
            role_arn=self.workspace_role.role_arn,
            plugin_admin_enabled=True,
            vpc_configuration=aws_grafana.CfnWorkspace.VpcConfigurationProperty(
                subnet_ids=vpc_construct.vpc.select_subnets(
                    selection=vpc_construct.private_subnet_selection
                ).get("subnetIds"),
                security_group_ids=[security_group.security_group_id],
            ),
        )

    def add_policy_to_grafana_workspace(self, policy: aws_iam.Policy) -> None:
        self.workspace_role.attach_inline_policy(policy)
