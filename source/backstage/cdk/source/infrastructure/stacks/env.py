# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
from typing import Any, List

# Third Party Libraries
from aws_cdk import Duration, Stack, Tags, aws_ec2, aws_kms, aws_rds, aws_s3, aws_ssm
from constructs import Construct

# Connected Mobility Solution on AWS
from ...config.constants import BackstageConstants


class BackstageEnvStack(Stack):
    def __init__(
        self, scope: Any, stack_id: str, *args: List[Any], **kwargs: Any
    ) -> None:
        super().__init__(scope, stack_id, *args, **kwargs)

        deployment_uuid = aws_ssm.StringParameter.from_string_parameter_name(
            self,
            "deployment-uuid",
            f"/{BackstageConstants.STAGE}/cms/common/config/deployment-uuid",
        ).string_value

        backstage_env_construct = BackstageEnvConstruct(self, "cms-backstage-env")

        Tags.of(backstage_env_construct).add(
            "Solutions:DeploymentUUID", deployment_uuid
        )


class BackstageEnvConstruct(Construct):
    def __init__(self, scope: Any, stack_id: str) -> None:
        super().__init__(scope, stack_id)
        vpc = aws_ec2.Vpc.from_lookup(
            self,
            f"{BackstageConstants.ENV_APP_NAME}-vpc-lookup",
            is_default=False,
            vpc_id=os.environ.get("BACKSTAGE_VPC_ID", "vpc_ic"),
        )

        pg_admin = aws_rds.Credentials.from_generated_secret(
            "backstage_pg_admin",
            secret_name=f"/{BackstageConstants.STAGE}/cms-backstage/backstage_pg_admin",
        )

        database_security_group = aws_ec2.SecurityGroup(
            self,
            "backstage-database-security-group",
            description="Backstage Database Security Group",
            vpc=vpc,
            allow_all_outbound=True,  # NOSONAR
        )

        self.parameter_group = aws_rds.ParameterGroup(
            self,
            "backstage-aurora-parameter-group",
            engine=aws_rds.DatabaseClusterEngine.aurora_postgres(
                version=aws_rds.AuroraPostgresEngineVersion.VER_13_9
            ),
        )

        self.database = aws_rds.ServerlessCluster(
            self,
            "backstage-aurora-postgres",
            engine=aws_rds.DatabaseClusterEngine.AURORA_POSTGRESQL,
            parameter_group=self.parameter_group,
            credentials=pg_admin,
            vpc=vpc,
            vpc_subnets=aws_ec2.SubnetSelection(subnets=vpc.private_subnets),
            deletion_protection=False,
            security_groups=[database_security_group],
        )

        self.database.add_rotation_single_user(
            automatically_after=Duration.days(90),
        )

        aws_ssm.StringParameter(
            self,
            "backstage-database-security-group-id",
            string_value=database_security_group.security_group_id,
            description="Backstage Database Security Group ID",
            parameter_name=f"/{BackstageConstants.STAGE}/{BackstageConstants.APP_NAME}/security-groups/backstage-database-security-group-id",
        )

        backstage_catalog_bucket_key = aws_kms.Key(
            self,
            "backstage-catalog-s3-key",
            enable_key_rotation=True,
        )

        backstage_catalog_bucket = aws_s3.Bucket(
            self,
            "backstage-catalog-bucket",
            block_public_access=aws_s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            server_access_logs_prefix="backstage-catalog-bucket/",
            encryption_key=backstage_catalog_bucket_key,
            versioned=True,
            encryption=aws_s3.BucketEncryption.KMS,
        )

        aws_ssm.StringParameter(
            self,
            "backstage-catalog-bucket-name",
            string_value=backstage_catalog_bucket.bucket_name,
            description="Backstage Catalog Bucket Name",
            parameter_name=f"/{BackstageConstants.STAGE}/{BackstageConstants.APP_NAME}/catalog-bucket/name",
        )

        aws_ssm.StringParameter(
            self,
            "backstage-catalog-bucket-region",
            string_value=Stack.of(self).region,
            description="Backstage Catalog Bucket Region",
            parameter_name=f"/{BackstageConstants.STAGE}/{BackstageConstants.APP_NAME}/catalog-bucket/region",
        )

        aws_ssm.StringParameter(
            self,
            "backstage-catalog-bucket-key-prefix",
            string_value="backstage/catalog",
            description="Bucket key prefix where Backstage Catalog Resources are to be published to",
            parameter_name=f"/{BackstageConstants.STAGE}/{BackstageConstants.APP_NAME}/config/catalog-key-prefix",
        )

        aws_ssm.StringParameter(
            self,
            "backstage-catalog-bucket-kms-key-arn",
            string_value=backstage_catalog_bucket_key.key_arn,
            description="Backstage Catalog Bucket KMS Key ARN",
            parameter_name=f"/{BackstageConstants.STAGE}/{BackstageConstants.APP_NAME}/catalog-bucket/kms-key-arn",
        )
