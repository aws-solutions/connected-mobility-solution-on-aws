# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

# Standard Library
from enum import Enum

# AWS Libraries
from aws_cdk import (
    ArnFormat,
    Duration,
    Stack,
    aws_ec2,
    aws_iam,
    aws_lambda,
    aws_logs,
    aws_ssm,
)
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

# Connected Mobility Solution on AWS
from ..module_integration import ModuleConfigInputs


class FleetWiseTimestreamTimeRangeHandler:
    class RequestType(Enum):
        GET = "Get"
        SET = "Set"

    @staticmethod
    def create_lambda(
        construct: Construct,
        solution_config_inputs: SolutionConfigInputs,
        module_config: ModuleConfigInputs,
        operational_metrics: OperationalMetricsInput,
        dependency_layer: aws_lambda.LayerVersion,
        vpc_construct: VpcConstruct,
    ) -> aws_lambda.Function:
        lambda_name = ResourceName.hyphen_separated(
            prefix=ResourcePrefix.hyphen_separated(
                app_unique_id=module_config.app_unique_id,
                module_name=solution_config_inputs.module_short_name,
            ),
            name="time-handler",
        )

        # Workaround for issue w/ CDK adding an extra slash to ARN with StringParameter.parameter_arn output and formatArn method.
        last_unload_end_time_ssm_parameter_name_without_slash_prefix = f"{module_config.module_ssm_prefix}/step-function/last-successful-execution/unload-end-timestamp"
        last_unload_end_time_ssm_parameter = aws_ssm.StringParameter(
            construct,
            "ssm-last-unload-end-time-parameter-name",
            string_value="UNSET",
            description="ISO Timestamp representing the last successful Timestream Unload Query end time",
            parameter_name=f"/{last_unload_end_time_ssm_parameter_name_without_slash_prefix}",
            simple_name=False,
        )

        lambda_role = FleetWiseTimestreamTimeRangeHandler._create_lambda_role(
            construct=construct,
            lambda_name=lambda_name,
            last_unload_end_time_ssm_parameter_name_without_slash_prefix=last_unload_end_time_ssm_parameter_name_without_slash_prefix,
            vpc_construct=vpc_construct,
        )

        lambda_function = aws_lambda.Function(
            construct,
            "time-range-handler-lambda",
            function_name=lambda_name,
            code=aws_lambda.Code.from_asset("dist/lambda/time_range_handler.zip"),
            description="CMS FleetWise Connector - Time Range Handler",
            environment={
                "REPORT_METRICS_ENABLED": operational_metrics.report_metrics_enabled,
                "METRICS_SOLUTION_URL": operational_metrics.metrics_url,
                "DEPLOYMENT_UUID": operational_metrics.deployment_uuid,
                "SOLUTION_ID": solution_config_inputs.solution_id,
                "SOLUTION_VERSION": solution_config_inputs.solution_version,
                "USER_AGENT_STRING": solution_config_inputs.get_user_agent_string(),
                "AWS_ACCOUNT_ID": Stack.of(construct).account,
                "UNLOAD_END_TIME_PARAMETER_NAME": last_unload_end_time_ssm_parameter.parameter_name,
            },
            handler="function.main.handler",
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            timeout=Duration.minutes(15),
            role=lambda_role,
            layers=[dependency_layer],
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
            vpc=vpc_construct.vpc,
            vpc_subnets=vpc_construct.private_subnet_selection,
            security_groups=[
                aws_ec2.SecurityGroup(
                    construct,
                    "time-range-handler-security-group",
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
        last_unload_end_time_ssm_parameter_name_without_slash_prefix: str,
        vpc_construct: VpcConstruct,
    ) -> aws_iam.Role:
        return aws_iam.Role(
            construct,
            "fleetwise-timestream-time-range-handler-role",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            path="/",
            inline_policies={
                "ssm-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=["ssm:GetParameter", "ssm:PutParameter"],
                            resources=[
                                Stack.of(construct).format_arn(
                                    service="ssm",
                                    resource="parameter",
                                    resource_name=last_unload_end_time_ssm_parameter_name_without_slash_prefix,
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                )
                            ],
                        ),
                    ]
                ),
                "timestream-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "timestream:DescribeEndpoints",
                                "timestream:SelectValues",
                            ],
                            resources=["*"],
                        )
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
