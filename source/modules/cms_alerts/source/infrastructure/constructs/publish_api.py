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
    aws_ec2,
    aws_iam,
    aws_lambda,
    aws_logs,
)
from constructs import Construct

# CMS Common Library
from cms_common.config.regex import RegexPattern
from cms_common.config.resource_names import ResourceName, ResourcePrefix
from cms_common.config.stack_inputs import SolutionConfigInputs
from cms_common.constructs.vpc_construct import VpcConstruct
from cms_common.policy_generators.cloudwatch import (
    generate_lambda_cloudwatch_logs_policy_document,
)
from cms_common.policy_generators.ec2_vpc import generate_ec2_vpc_policy
from cms_common.policy_generators.kms import generate_kms_policy_statement_from_key_id


class PublishApiConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_unique_id: str,
        solution_config_inputs: SolutionConfigInputs,
        authorization_lambda: aws_lambda.Function,
        dependency_layer: aws_lambda.LayerVersion,
        sns_topic_arn: str,
        sns_topic_key_id: str,
        vpc_construct: VpcConstruct,
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
            "graphql-publish-api",
            name=ResourceName.hyphen_separated(
                prefix=ResourcePrefix.hyphen_separated(
                    app_unique_id=app_unique_id,
                    module_name=solution_config_inputs.module_short_name,
                ),
                name="publish-api",
            ),
            schema=aws_appsync.SchemaFile.from_asset(
                "source/graphql/publish_api.graphql"
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

        appsync_api_log_role.node.try_remove_child("DefaultPolicy")

        publish_lambda_name = ResourceName.hyphen_separated(
            prefix=ResourcePrefix.hyphen_separated(
                app_unique_id=app_unique_id,
                module_name=solution_config_inputs.module_short_name,
            ),
            name="publish",
        )

        publish_lambda = aws_lambda.Function(
            self,
            "publish-lambda",
            function_name=publish_lambda_name,
            code=aws_lambda.Code.from_asset("deployment/dist/lambda/publish.zip"),
            description="CMS Alerts Publish Function",
            environment={
                "USER_AGENT_STRING": solution_config_inputs.get_user_agent_string(),
                "ALERTS_SNS_TOPIC_ARN": sns_topic_arn,
            },
            handler="main.handler",
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            timeout=Duration.minutes(1),
            role=aws_iam.Role(
                self,
                "publish-lambda-role",
                assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
                inline_policies={
                    "sns-policy": aws_iam.PolicyDocument(
                        statements=[
                            aws_iam.PolicyStatement(
                                effect=aws_iam.Effect.ALLOW,
                                actions=["sns:Publish"],
                                resources=[sns_topic_arn],
                            ),
                            generate_kms_policy_statement_from_key_id(
                                self, sns_topic_key_id, True
                            ),
                        ]
                    ),
                    "cloudwatch-policy": generate_lambda_cloudwatch_logs_policy_document(
                        self, publish_lambda_name
                    ),
                    "ec2-policy": generate_ec2_vpc_policy(
                        self,
                        vpc_construct=vpc_construct,
                        subnet_selection=vpc_construct.private_subnet_selection,
                        authorized_service="lambda.amazonaws.com",
                    ),
                },
            ),
            layers=[dependency_layer],
            vpc=vpc_construct.vpc,
            vpc_subnets=vpc_construct.private_subnet_selection,
            security_groups=[
                aws_ec2.SecurityGroup(
                    self,
                    "security-group",
                    vpc=vpc_construct.vpc,
                    allow_all_outbound=True,  # NOSONAR
                )
            ],
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
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
                            resources=[publish_lambda.function_arn],
                        )
                    ]
                )
            },
        )

        lambda_ds = aws_appsync.LambdaDataSource(
            self,
            "alerts-api-publish-lambda-data-source",
            lambda_function=publish_lambda,
            api=self.graphql_api,
            service_role=graphql_api_service_role,
        )

        graphql_api_service_role.node.try_remove_child("DefaultPolicy")

        lambda_ds.create_resolver(
            "publish-user-preferences-resolver",
            type_name="Mutation",
            field_name="publish",
        )
