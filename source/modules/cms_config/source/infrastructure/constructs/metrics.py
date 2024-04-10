# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any

# AWS Libraries
from aws_cdk import (
    Aspects,
    CfnCondition,
    CfnMapping,
    Duration,
    Fn,
    Stack,
    aws_ec2,
    aws_events,
    aws_events_targets,
    aws_iam,
    aws_lambda,
    aws_logs,
)
from constructs import Construct

# CMS Common Library
from cms_common.aspects.condition import ConditionAspect
from cms_common.config.stack_inputs import SolutionConfigInputs
from cms_common.constructs.vpc_construct import VpcConstruct
from cms_common.policy_generators.cloudwatch import (
    generate_lambda_cloudwatch_logs_policy_document,
)
from cms_common.policy_generators.ec2_vpc import generate_ec2_vpc_policy


class MetricsConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        stack_id: str,
        metrics_url: str,
        deployment_uuid: str,
        dependency_layer: aws_lambda.LayerVersion,
        solution_mapping: CfnMapping,
        solution_config_inputs: SolutionConfigInputs,
        metrics_lambda_function_name: str,
        vpc_construct: VpcConstruct,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, stack_id, **kwargs)

        metrics_lambda_role = aws_iam.Role(
            self,
            "lambda-role",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            inline_policies={
                "lambda-logs-policy": generate_lambda_cloudwatch_logs_policy_document(
                    self, metrics_lambda_function_name
                ),
                "cloudwatch-metrics-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "cloudwatch:GetMetricData",
                                "cloudwatch:GetMetricStatistics",
                                "cloudwatch:ListMetrics",
                            ],
                            # cloudwatch:Get*/List* does not support any kind of access control (https://docs.aws.amazon.com/service-authorization/latest/reference/list_amazoncloudwatch.html)
                            resources=["*"],
                        )
                    ]
                ),
                "resourcegroupstaggingapi-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "tag:GetResources",
                                "tag:GetTagKeys",
                                "tag:GetTagValues",
                            ],
                            resources=["*"],
                        )
                    ]
                ),
                "ec2-policy": generate_ec2_vpc_policy(
                    self,
                    vpc_construct=vpc_construct,
                    subnet_selection=vpc_construct.private_subnet_selection,
                    authorized_service="lambda.amazonaws.com",
                ),
            },
        )

        metrics_lambda_function = aws_lambda.Function(
            self,
            "lambda-function",
            code=aws_lambda.Code.from_asset(
                "dist/lambda/metrics.zip",
                exclude=["**/tests/*"],
            ),
            handler="function.main.handler",
            function_name=metrics_lambda_function_name,
            role=metrics_lambda_role,
            runtime=aws_lambda.Runtime.PYTHON_3_10,
            timeout=Duration.seconds(300),
            layers=[dependency_layer],
            environment={
                "USER_AGENT_STRING": solution_config_inputs.get_user_agent_string(),
                "SOLUTION_ID": solution_config_inputs.solution_id,
                "SOLUTION_VERSION": solution_config_inputs.solution_version,
                "AWS_ACCOUNT_ID": Stack.of(self).account,
                "DEPLOYMENT_UUID": deployment_uuid,
                "METRICS_SOLUTION_URL": metrics_url,
            },
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
            vpc=vpc_construct.vpc,
            vpc_subnets=vpc_construct.private_subnet_selection,
            security_groups=[
                aws_ec2.SecurityGroup(
                    self,
                    "security-group",
                    allow_all_outbound=True,  # NOSONAR
                    vpc=vpc_construct.vpc,
                )
            ],
        )

        event_rule = aws_events.Rule(
            self,
            "cron-rule",
            schedule=aws_events.Schedule.cron(hour="1", minute="0"),
        )

        event_rule.add_target(
            target=aws_events_targets.LambdaFunction(metrics_lambda_function)
        )

        self.send_anonymous_usage = solution_mapping.find_in_map(
            "Config", "SendAnonymousUsage"
        )

        self.send_anonymous_usage_condition = CfnCondition(
            scope,
            "SendAnonymousUsage",
            expression=Fn.condition_equals(self.send_anonymous_usage, "Yes"),
        )

        Aspects.of(self).add(ConditionAspect(self.send_anonymous_usage_condition))
