# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
from os.path import abspath, dirname
from pathlib import Path
from typing import Any

# Third Party Libraries
import toml
from aws_cdk import (
    Duration,
    RemovalPolicy,
    Stack,
    aws_events,
    aws_events_targets,
    aws_iam,
    aws_lambda,
    aws_logs,
)
from constructs import Construct

# Connected Mobility Solution on AWS
from ...stacks import CmsConstants, generate_lambda_cloudwatch_logs_policy_document


class Metrics(Construct):
    def __init__(  # pylint: disable=too-many-locals
        self,
        scope: Stack,
        stack_id: str,
        metrics_url: str,
        deployment_uuid: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, stack_id, **kwargs)

        metrics_lambda_name = f"{CmsConstants.STACK_NAME}-anonymous-metrics-reporting"

        metrics_lambda_role = aws_iam.Role(
            self,
            "metrics-reporting-lambda-role",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            inline_policies={
                "lambda-logs-policy": generate_lambda_cloudwatch_logs_policy_document(
                    self, metrics_lambda_name
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
                            resources=[
                                "*"
                            ],  # cloudwatch:Get*/List* does not support any kind of access control (https://docs.aws.amazon.com/service-authorization/latest/reference/list_amazoncloudwatch.html)
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
            },
        )

        dependency_layer_name = "cms_metrics_dependency_layer"

        metrics_function = aws_lambda.Function(
            self,
            "cmdp-metrics-lambda",
            code=aws_lambda.Code.from_asset(
                "source/infrastructure/handlers/metrics", exclude=["**/tests/*"]
            ),
            handler="app.main.lambda_handler",  # Must place in nested folder to resolve lambda relative import issue: https://gist.github.com/gene1wood/06a64ba80cf3fe886053f0ca6d375bc0
            function_name=metrics_lambda_name,
            role=metrics_lambda_role,
            runtime=aws_lambda.Runtime.PYTHON_3_10,
            timeout=Duration.seconds(300),
            layers=[
                self.package_dependency_layer(
                    dir_path=f"{os.getcwd()}/{self.node.try_get_context('app-location')}/{dependency_layer_name}",
                    dependency_layer_name=dependency_layer_name,
                ),
            ],
            environment={
                "USER_AGENT_STRING": CmsConstants.USER_AGENT_STRING,
                "SOLUTION_ID": CmsConstants.SOLUTION_ID,
                "SOLUTION_VERSION": CmsConstants.SOLUTION_VERSION,
                "AWS_ACCOUNT_ID": Stack.of(self).account,
                "DEPLOYMENT_UUID": deployment_uuid,
                "METRICS_SOLUTION_URL": metrics_url,
            },
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
        )

        event_rule = aws_events.Rule(
            self,
            "metrics-lambda-cron-rule",
            schedule=aws_events.Schedule.cron(hour="1", minute="0"),
        )

        event_rule.add_target(
            target=aws_events_targets.LambdaFunction(metrics_function)
        )

    def package_dependency_layer(
        self, dir_path: str, dependency_layer_name: str
    ) -> aws_lambda.LayerVersion:
        source_pipfile = f"{dirname(dirname(dirname(abspath(__file__))))}/../../Pipfile"
        pip_path = f"{dir_path}/python"

        # Create the folders out to the build directory
        Path(pip_path).mkdir(parents=True, exist_ok=True)
        requirements = f"{dir_path}/requirements.txt"
        exclude_list = ["chalice", "aws-cdk-lib", "boto3"]
        # Copy Pipfile to build directory as requirements.txt format and excluding the large packages
        with open(source_pipfile, "r", encoding="utf-8") as pipfile:
            new_pipfile = toml.load(pipfile)
        with open(requirements, "w", encoding="utf-8") as req_file:

            def req_formatter(package: str, constraint: Any) -> None:
                if constraint == "*":
                    req_file.write(package + "\n")
                    return

                try:
                    extras = (
                        str(constraint.get("extras", "all"))
                        .replace("'", "")
                        .replace('"', "")
                    )
                    version = (
                        constraint["version"] if constraint["version"] != "*" else ""
                    )
                    req_file.write(f"{package}{extras} {version}\n")
                except (TypeError, KeyError, AttributeError):
                    if isinstance(constraint, str):
                        req_file.write(f"{package} {constraint}\n")

            for package, constraint in new_pipfile["packages"].items():
                if package not in exclude_list:
                    req_formatter(package, constraint)

        # Install the requirements in the build directory (CDK will use this whole folder to build the zip)
        os.system(  # nosec
            f"/bin/bash -c 'python -m pip install -q --upgrade --target {pip_path} --requirement {requirements}'"
        )

        dependency_layer = aws_lambda.LayerVersion(
            self,
            "metrics-dependency-layer-version",
            removal_policy=RemovalPolicy.DESTROY,
            code=aws_lambda.Code.from_asset(
                f"{os.getcwd()}/{self.node.try_get_context('app-location')}/{dependency_layer_name}"
            ),
            compatible_architectures=[
                aws_lambda.Architecture.X86_64,
                aws_lambda.Architecture.ARM_64,
            ],
            compatible_runtimes=[
                aws_lambda.Runtime.PYTHON_3_8,
                aws_lambda.Runtime.PYTHON_3_9,
                aws_lambda.Runtime.PYTHON_3_10,
            ],
        )

        return dependency_layer
