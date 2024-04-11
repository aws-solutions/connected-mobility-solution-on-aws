# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# AWS Libraries
from aws_cdk import (
    ArnFormat,
    Duration,
    Stack,
    aws_appsync,
    aws_iam,
    aws_lambda,
    aws_logs,
)
from constructs import Construct


class AppSyncAPIConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        name: str,
        schema_path: str,
        authorization_lambda: aws_lambda.IFunction,
    ) -> None:
        super().__init__(scope, construct_id)

        appsync_api_log_role = aws_iam.Role(
            self,
            "graphql-api-access-log-role",
            assumed_by=aws_iam.ServicePrincipal("appsync.amazonaws.com"),
            path="/",
        )
        self.graphql_api = aws_appsync.GraphqlApi(
            self,
            "graphql-api",
            name=name,
            schema=aws_appsync.SchemaFile.from_asset(schema_path),
            authorization_config=aws_appsync.AuthorizationConfig(
                default_authorization=aws_appsync.AuthorizationMode(
                    authorization_type=aws_appsync.AuthorizationType.LAMBDA,
                    lambda_authorizer_config=aws_appsync.LambdaAuthorizerConfig(
                        handler=authorization_lambda,
                        results_cache_ttl=Duration.minutes(5),
                        validation_regex=r"^Bearer [\w-]+\.[\w-]+\.[\w-]+$",
                    ),
                )
            ),
            log_config=aws_appsync.LogConfig(
                retention=aws_logs.RetentionDays.THREE_MONTHS, role=appsync_api_log_role
            ),
            xray_enabled=True,
        )
        appsync_api_log_role.add_to_policy(
            aws_iam.PolicyStatement(
                effect=aws_iam.Effect.ALLOW,
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                ],
                resources=[
                    Stack.of(self).format_arn(
                        service="logs",
                        resource="log-group",
                        resource_name=f"/aws/appsync/apis/{self.graphql_api.api_id}",
                        arn_format=ArnFormat.COLON_RESOURCE_NAME,
                    ),
                    Stack.of(self).format_arn(
                        service="logs",
                        resource="log-group",
                        resource_name=f"/aws/appsync/apis/{self.graphql_api.api_id}:log-stream:*",
                        arn_format=ArnFormat.COLON_RESOURCE_NAME,
                    ),
                ],
            )
        )
