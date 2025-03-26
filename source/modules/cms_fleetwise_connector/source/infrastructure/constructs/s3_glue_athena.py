# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# IMPLEMENT: Insert IAM roles/policies required by FW to connect to Timestream
# SEE: https://docs.aws.amazon.com/iot-fleetwise/latest/developerguide/controlling-access.html

# AWS Libraries
from aws_cdk import ArnFormat, Stack, aws_ec2, aws_glue, aws_iam
from constructs import Construct

# CMS Common Library
from cms_common.config.resource_names import ResourceName, ResourcePrefix
from cms_common.config.stack_inputs import SolutionConfigInputs
from cms_common.constructs.vpc_construct import VpcConstruct
from cms_common.constructs.vpc_prefix_list_lookup_custom_resource import (
    VpcPrefixListLookupCustomResourceConstruct,
)
from cms_common.policy_generators.ec2_vpc import generate_ec2_vpc_policy

# Connected Mobility Solution on AWS
from .module_integration import ModuleConfigInputs, TelemetryBucketInputs


class S3GlueAthenaConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        module_config: ModuleConfigInputs,
        solution_config_inputs: SolutionConfigInputs,
        telemetry_bucket: TelemetryBucketInputs,
        vpc_construct: VpcConstruct,
    ) -> None:
        super().__init__(scope, construct_id)

        glue_crawler_name = ResourceName.hyphen_separated(
            prefix=ResourcePrefix.hyphen_separated(
                app_unique_id=module_config.app_unique_id,
                module_name=solution_config_inputs.module_short_name,
            ),
            name="data",
        )
        glue_database_name = ResourcePrefix.hyphen_separated(
            app_unique_id=module_config.app_unique_id,
            module_name=solution_config_inputs.module_short_name,
        )
        glue_table_prefix = "fleetwise-data-"

        security_configuration = aws_glue.CfnSecurityConfiguration(
            self,
            "security-configuration",
            name=f"{glue_crawler_name}-security",
            encryption_configuration=aws_glue.CfnSecurityConfiguration.EncryptionConfigurationProperty(
                cloud_watch_encryption=aws_glue.CfnSecurityConfiguration.CloudWatchEncryptionProperty(
                    cloud_watch_encryption_mode="DISABLED",
                ),
                s3_encryptions=[
                    aws_glue.CfnSecurityConfiguration.S3EncryptionProperty(
                        s3_encryption_mode="SSE-S3",
                    )
                ],
            ),
        )

        role = aws_iam.Role(
            self,
            "glue-crawler-role",
            assumed_by=aws_iam.ServicePrincipal("glue.amazonaws.com"),
            inline_policies={
                "s3-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "s3:GetObject",
                                "s3:PutObject",
                                "s3:ListBucket",
                                "s3:GetBucketAcl",
                            ],
                            resources=[
                                telemetry_bucket.bucket_arn,
                                f"{telemetry_bucket.bucket_arn}/{module_config.timestream_unload_s3_prefix_path}/*",
                            ],
                        ),
                    ]
                ),
                "glue-security-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            actions=[
                                "glue:GetSecurityConfiguration",
                                "glue:GetSecurityConfigurations",
                                "glue:GetConnection",
                                "glue:GetConnections",
                            ],
                            resources=["*"],  # NOSONAR
                        )
                    ]
                ),
                "glue-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            actions=[
                                "glue:CreateDatabase",
                                "glue:CreateTable",
                                "glue:CreatePartition",
                                "glue:CreatePartitionIndex",
                                "glue:GetDatabase",
                                "glue:GetDatabases",
                                "glue:GetTable",
                                "glue:GetTables",
                                "glue:GetSecurityConfiguration",
                                "glue:GetSecurityConfigurations",
                                "glue:BatchGetPartition",
                                "glue:BatchCreatePartition",
                                "glue:UpdateDatabase",
                                "glue:UpdateTable",
                                "glue:UpdatePartition",
                                "glue:DeleteTable",
                                "glue:DeletePartition",
                                "glue:BatchDeletePartition",
                                "glue:BatchDeleteTable",
                                "glue:BatchDeleteTableVersion",
                            ],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="glue",
                                    resource="security-configuration",
                                    resource_name=security_configuration.name,
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                                Stack.of(self).format_arn(
                                    service="glue",
                                    resource="catalog",
                                    arn_format=ArnFormat.NO_RESOURCE_NAME,
                                ),
                                Stack.of(self).format_arn(
                                    service="glue",
                                    resource="database",
                                    resource_name=glue_database_name,
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                                Stack.of(self).format_arn(
                                    service="glue",
                                    resource="table",
                                    resource_name=f"{glue_database_name}/{glue_table_prefix}*",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                            ],
                        )
                    ]
                ),
                "ec2-vpc-policy": generate_ec2_vpc_policy(
                    self,
                    vpc_construct=vpc_construct,
                    subnet_selection=vpc_construct.private_subnet_selection,
                    authorized_service="glue.amazonaws.com",
                ),
                "ec2-vpc-policy-glue": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "ec2:DescribeSubnets",
                                "ec2:DescribeAvailabilityZones",
                                "ec2:DescribeNetworkAcls",
                                "ec2:DescribeRouteTables",
                                "ec2:DescribeVpcEndpoints",
                                "ec2:DescribeSecurityGroups",
                                "ec2:CreateTags",
                            ],
                            resources=["*"],  # NOSONAR
                            conditions={
                                "StringEquals": {"ec2:Region": [Stack.of(self).region]}
                            },
                        )
                    ]
                ),
                "logs-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "logs:CreateLogGroup",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents",
                                "logs:AssociateKmsKey",
                            ],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="logs",
                                    resource="log-group",
                                    resource_name="/aws-glue/crawlers",
                                    arn_format=ArnFormat.COLON_RESOURCE_NAME,
                                ),
                                Stack.of(self).format_arn(
                                    service="logs",
                                    resource="log-group",
                                    resource_name="/aws-glue/crawlers:*",
                                    arn_format=ArnFormat.COLON_RESOURCE_NAME,
                                ),
                                Stack.of(self).format_arn(
                                    service="logs",
                                    resource="log-group",
                                    resource_name="/aws-glue/crawlers-role/*",
                                    arn_format=ArnFormat.COLON_RESOURCE_NAME,
                                ),
                            ],
                        ),
                    ]
                ),
            },
        )

        glue_security_group = aws_ec2.SecurityGroup(
            self,
            "glue-crawler-security-group",
            vpc=vpc_construct.vpc,
            description="Allow all inbound and outbound traffic as required by Glue.",
            allow_all_outbound=False,
        )
        glue_security_group.add_ingress_rule(
            peer=glue_security_group,
            connection=aws_ec2.Port.all_traffic(),
            description="Allow all inbound traffic from the Security Group to itself",
        )
        glue_security_group.add_egress_rule(
            peer=glue_security_group,
            connection=aws_ec2.Port.all_traffic(),
            description="Allow all outbound traffic from the Security Group to itself",
        )
        s3_prefix_list_id = VpcPrefixListLookupCustomResourceConstruct(
            self,
            "prefix-list-lookup",
            app_unique_id=module_config.app_unique_id,
            module_name=solution_config_inputs.module_short_name,
            vpc_construct=vpc_construct,
            prefix_list_name=f"com.amazonaws.{Stack.of(self).region}.s3",
        ).prefix_list_id

        glue_security_group.add_egress_rule(
            peer=aws_ec2.Peer.prefix_list(s3_prefix_list_id),
            connection=aws_ec2.Port.all_tcp(),
            description="Allow outbound traffic to the s3 endpoint",
        )

        glue_connection_name = f"{glue_crawler_name}-connection"
        glue_connection = aws_glue.CfnConnection(
            self,
            "crawler-connection",
            catalog_id=Stack.of(self).account,
            connection_input=aws_glue.CfnConnection.ConnectionInputProperty(
                name=glue_connection_name,
                connection_type="NETWORK",
                physical_connection_requirements=aws_glue.CfnConnection.PhysicalConnectionRequirementsProperty(
                    availability_zone=vpc_construct.vpc.availability_zones[0],
                    subnet_id=vpc_construct.private_subnets[0].subnet_id,
                    security_group_id_list=[glue_security_group.security_group_id],
                ),
            ),
        )

        glue_crawler = aws_glue.CfnCrawler(
            self,
            "crawler",
            role=role.role_arn,
            name=glue_crawler_name,
            database_name=glue_database_name,
            table_prefix=glue_table_prefix,
            recrawl_policy=aws_glue.CfnCrawler.RecrawlPolicyProperty(
                recrawl_behavior="CRAWL_EVERYTHING"
            ),
            schedule=aws_glue.CfnCrawler.ScheduleProperty(
                schedule_expression=module_config.glue_crawler_cron_expression,
            ),  # Run every hour
            targets=aws_glue.CfnCrawler.TargetsProperty(
                s3_targets=[
                    aws_glue.CfnCrawler.S3TargetProperty(
                        path=f"s3://{telemetry_bucket.bucket_name}/{module_config.timestream_unload_s3_prefix_path}/results/",
                        connection_name=glue_connection_name,
                    )
                ]
            ),
            crawler_security_configuration=security_configuration.name,
        )
        glue_crawler.node.add_dependency(glue_connection)
