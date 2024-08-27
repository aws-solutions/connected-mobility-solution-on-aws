# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any

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

# CMS Common Library
from cms_common.config.regex import RegexPattern
from cms_common.config.resource_names import ResourceName, ResourcePrefix
from cms_common.config.stack_inputs import SolutionConfigInputs


class FrontendApisConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_unique_id: str,
        solution_config_inputs: SolutionConfigInputs,
        user_subscriptions_lambda: aws_lambda.Function,
        authorization_lambda: aws_lambda.Function,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        appsync_api_log_role = aws_iam.Role(
            self,
            "graphql-api-access-log-role",
            assumed_by=aws_iam.ServicePrincipal("appsync.amazonaws.com"),
            path="/",
        )

        self.graphql_api = aws_appsync.GraphqlApi(
            self,
            "appsync-api",
            name=ResourceName.hyphen_separated(
                prefix=ResourcePrefix.hyphen_separated(
                    app_unique_id=app_unique_id,
                    module_name=solution_config_inputs.module_short_name,
                ),
                name="frontend-api",
            ),
            schema=aws_appsync.SchemaFile.from_asset(
                "source/graphql/user_subscriptions_api.graphql"
            ),
            authorization_config=aws_appsync.AuthorizationConfig(
                default_authorization=aws_appsync.AuthorizationMode(
                    authorization_type=aws_appsync.AuthorizationType.LAMBDA,
                    lambda_authorizer_config=aws_appsync.LambdaAuthorizerConfig(
                        handler=authorization_lambda,
                        results_cache_ttl=Duration.minutes(5),
                        validation_regex=RegexPattern.BEARER_TOKEN_AUTH_HEADER,
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

        graphql_api_service_role = aws_iam.Role(
            self,
            "graphql-api-service-role",
            assumed_by=aws_iam.ServicePrincipal("appsync.amazonaws.com"),
            inline_policies={
                "lambda-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=["lambda:InvokeFunction"],
                            resources=[user_subscriptions_lambda.function_arn],
                        )
                    ]
                )
            },
        )

        lambda_ds = aws_appsync.LambdaDataSource(
            self,
            "alerts-api-user-subscriptions-lambda-data-source",
            lambda_function=user_subscriptions_lambda,
            api=self.graphql_api,
            service_role=graphql_api_service_role,
        )

        graphql_api_service_role.node.try_remove_child("DefaultPolicy")

        lambda_ds.create_resolver(
            "get-user-subscriptions-resolver",
            type_name="Query",
            field_name="getUserSubscriptions",
        )
        lambda_ds.create_resolver(
            "update-user-subscriptions-resolver",
            type_name="Mutation",
            field_name="updateUserSubscriptions",
        )
