# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# AWS Libraries
from aws_cdk import Duration, aws_ec2, aws_rds
from constructs import Construct


class AuroraDatabaseConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        vpc: aws_ec2.IVpc,
        isolated_subnets: aws_ec2.SubnetSelection,
        credentials_secret_name: str,
        cluster_engine: aws_rds.IClusterEngine,
        rotation_interval_days: Duration,
    ) -> None:
        super().__init__(scope, construct_id)

        self.database_credentials_secret = aws_rds.DatabaseSecret(
            self,
            "database-secret",
            username="db_admin",
            secret_name=credentials_secret_name,
        )

        self.database_security_group = aws_ec2.SecurityGroup(
            self, "database-security-group", vpc=vpc, allow_all_outbound=False
        )

        database = aws_rds.DatabaseCluster(
            self,
            "aurora-serverless-v2-cluster",
            engine=cluster_engine,
            serverless_v2_min_capacity=1,
            serverless_v2_max_capacity=8,
            writer=aws_rds.ClusterInstance.serverless_v2("writer"),
            credentials=aws_rds.Credentials.from_secret(
                self.database_credentials_secret
            ),
            vpc=vpc,
            vpc_subnets=isolated_subnets,
            security_groups=[self.database_security_group],
            deletion_protection=False,
            storage_encrypted=True,
        )

        database.add_rotation_single_user(
            automatically_after=rotation_interval_days,
            security_group=self.database_security_group,
        )
