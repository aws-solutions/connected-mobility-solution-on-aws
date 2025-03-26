# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

# AWS Libraries
from aws_cdk import Duration, Stack, aws_ec2, aws_iam, aws_lambda, aws_logs
from constructs import Construct

# CMS Common Library
from cms_common.config.metrics import OperationalMetricsInput
from cms_common.config.resource_names import ResourceName, ResourcePrefix
from cms_common.config.stack_inputs import SolutionConfigInputs
from cms_common.constructs.vpc_construct import VpcConstruct
from cms_common.policy_generators.cloudwatch import (
    generate_lambda_cloudwatch_logs_policy_document,
)
from cms_common.policy_generators.ec2_vpc import generate_ec2_vpc_policy
from cms_common.policy_generators.kms import generate_kms_policy_statement_from_key_arn

# Connected Mobility Solution on AWS
from ..module_integration import TimestreamOutputs


class FleetWiseTimestreamQueryVin:
    @staticmethod
    def create_lambda(
        construct: Construct,
        app_unique_id: str,
        solution_config_inputs: SolutionConfigInputs,
        timestream: TimestreamOutputs,
        operational_metrics: OperationalMetricsInput,
        vpc_construct: VpcConstruct,
    ) -> aws_lambda.Function:
        lambda_name = ResourceName.hyphen_separated(
            prefix=ResourcePrefix.hyphen_separated(
                app_unique_id=app_unique_id,
                module_name=solution_config_inputs.module_short_name,
            ),
            name="timestream-vin-query",
        )

        lambda_role = FleetWiseTimestreamQueryVin._create_lambda_role(
            construct=construct,
            lambda_name=lambda_name,
            timestream=timestream,
            vpc_construct=vpc_construct,
        )

        lambda_function = aws_lambda.Function(
            construct,
            "timestream-query-vins-lambda",
            function_name=lambda_name,
            code=aws_lambda.Code.from_asset(
                "deployment/dist/lambda/query_vehicle_vins.zip"
            ),
            description="CMS FleetWise Connector - Query Timestream VINs",
            environment={
                "REPORT_METRICS_ENABLED": operational_metrics.report_metrics_enabled,
                "METRICS_SOLUTION_URL": operational_metrics.metrics_url,
                "DEPLOYMENT_UUID": operational_metrics.deployment_uuid,
                "SOLUTION_ID": solution_config_inputs.solution_id,
                "SOLUTION_VERSION": solution_config_inputs.solution_version,
                "USER_AGENT_STRING": solution_config_inputs.get_user_agent_string(),
                "AWS_ACCOUNT_ID": Stack.of(construct).account,
            },
            handler="function.main.handler",
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            timeout=Duration.minutes(15),
            role=lambda_role,
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
            vpc=vpc_construct.vpc,
            vpc_subnets=vpc_construct.private_subnet_selection,
            security_groups=[
                aws_ec2.SecurityGroup(
                    construct,
                    "timestream-query-vins-security-group",
                    vpc=vpc_construct.vpc,
                    allow_all_outbound=True,  # NOSONAR
                )
            ],
        )

        return lambda_function

    @staticmethod
    def _create_lambda_role(
        construct: Construct,
        lambda_name: str,
        timestream: TimestreamOutputs,
        vpc_construct: VpcConstruct,
    ) -> aws_iam.Role:
        return aws_iam.Role(
            construct,
            "fleetwise-timestream-query-vins-lambda-role",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            path="/",
            inline_policies={
                "timestream-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "timestream:ListMeasures",
                                "timestream:Select",
                            ],
                            resources=[timestream.table_arn],
                        ),
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "timestream:DescribeEndpoints",
                            ],
                            resources=["*"],
                        ),
                        generate_kms_policy_statement_from_key_arn(
                            timestream.timestream_key_arn, True
                        ),
                    ]
                ),
                "lambda-logs-policy": generate_lambda_cloudwatch_logs_policy_document(
                    construct, lambda_name
                ),
                "ec2-vpc-policy": generate_ec2_vpc_policy(
                    construct,
                    vpc_construct=vpc_construct,
                    subnet_selection=vpc_construct.private_subnet_selection,
                    authorized_service="lambda.amazonaws.com",
                ),
            },
        )
