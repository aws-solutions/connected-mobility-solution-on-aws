# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
from aws_cdk import (
    Duration,
    RemovalPolicy,
    aws_iam,
    aws_kms,
    aws_lambda,
    aws_lambda_event_sources,
    aws_logs,
    aws_s3,
)
from constructs import Construct

# Connected Mobility Solution on AWS
from ...config.constants import EVBatteryHealthConstants
from ..lib.policy_generators import (
    generate_kms_policy_statement,
    generate_lambda_cloudwatch_logs_policy_document,
)


class S3ToGrafanaConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        dependency_layer: aws_lambda.LayerVersion,
        grafana_api_key_secret_arn: str,
        grafana_workspace_endpoint: str,
    ) -> None:
        super().__init__(scope, construct_id)

        sever_access_logs_s3_key = aws_kms.Key(
            self,
            "assets-server-access-logs-s3-key",
            enable_key_rotation=True,
            removal_policy=RemovalPolicy.DESTROY,
        )

        server_access_logs_bucket = aws_s3.Bucket(
            self,
            "assets-server-access-logs-bucket",
            enforce_ssl=True,
            encryption=aws_s3.BucketEncryption.KMS,
            encryption_key=sever_access_logs_s3_key,
            block_public_access=aws_s3.BlockPublicAccess.BLOCK_ALL,
            versioned=True,
        )

        self.s3_key = aws_kms.Key(
            self,
            "assets-s3-key",
            enable_key_rotation=True,
            removal_policy=RemovalPolicy.DESTROY,
        )

        self.s3_bucket = aws_s3.Bucket(
            self,
            "assets-s3-bucket",
            enforce_ssl=True,
            encryption_key=self.s3_key,
            encryption=aws_s3.BucketEncryption.KMS,
            server_access_logs_bucket=server_access_logs_bucket,
            block_public_access=aws_s3.BlockPublicAccess.BLOCK_ALL,
            versioned=True,
            auto_delete_objects=True,
            removal_policy=RemovalPolicy.DESTROY,
        )

        s3_to_grafana_lambda_function_name = (
            f"{EVBatteryHealthConstants.APP_NAME}-s3-to-grafana-lambda"
        )

        s3_to_grafana_lambda_role = aws_iam.Role(
            self,
            "lambda-role",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            inline_policies={
                "secretsmanager-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            actions=[
                                "secretsmanager:GetSecretValue",
                            ],
                            effect=aws_iam.Effect.ALLOW,
                            resources=[
                                grafana_api_key_secret_arn,
                            ],
                        ),
                    ]
                ),
                "s3-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            actions=[
                                "s3:GetObject",
                            ],
                            effect=aws_iam.Effect.ALLOW,
                            resources=[
                                f"{self.s3_bucket.bucket_arn}/{EVBatteryHealthConstants.DASHBOARD_S3_OBJECT_KEY_PREFIX}*",
                                f"{self.s3_bucket.bucket_arn}/{EVBatteryHealthConstants.ALERTS_S3_OBJECT_KEY_PREFIX}*",
                            ],
                        ),
                        generate_kms_policy_statement(
                            kms_encryption_key_arn=self.s3_key.key_arn,
                            allow_encrypt=False,
                        ),
                    ]
                ),
                "cloudwatch-policy": generate_lambda_cloudwatch_logs_policy_document(
                    self,
                    lambda_function_name=s3_to_grafana_lambda_function_name,
                ),
            },
        )

        s3_to_grafana_lambda = aws_lambda.Function(
            self,
            "lambda-function",
            description="CMS EV battery health update s3 assets to grafana lambda function",
            handler="s3_to_grafana.main.handler",
            function_name=s3_to_grafana_lambda_function_name,
            runtime=aws_lambda.Runtime.PYTHON_3_10,
            code=aws_lambda.Code.from_asset("source/handlers"),
            timeout=Duration.seconds(60),
            role=s3_to_grafana_lambda_role,
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
            layers=[dependency_layer],
            environment={
                "USER_AGENT_STRING": EVBatteryHealthConstants.USER_AGENT_STRING,
                "GRAFANA_API_KEY_SECRET_ARN": grafana_api_key_secret_arn,
                "GRAFANA_WORKSPACE_ENDPOINT": grafana_workspace_endpoint,
                "DASHBOARD_S3_OBJECT_KEY_PREFIX": EVBatteryHealthConstants.DASHBOARD_S3_OBJECT_KEY_PREFIX,
                "ALERTS_S3_OBJECT_KEY_PREFIX": EVBatteryHealthConstants.ALERTS_S3_OBJECT_KEY_PREFIX,
            },
        )

        # call the s3 to grafana lambda whenever an object with desired prefix
        # is uploaded to the s3 bucket
        dashboard_s3_event_source = aws_lambda_event_sources.S3EventSource(
            bucket=self.s3_bucket,
            events=[aws_s3.EventType.OBJECT_CREATED],
            filters=[
                aws_s3.NotificationKeyFilter(
                    prefix=EVBatteryHealthConstants.DASHBOARD_S3_OBJECT_KEY_PREFIX,
                ),
            ],
        )
        alerts_s3_event_source = aws_lambda_event_sources.S3EventSource(
            bucket=self.s3_bucket,
            events=[aws_s3.EventType.OBJECT_CREATED],
            filters=[
                aws_s3.NotificationKeyFilter(
                    prefix=EVBatteryHealthConstants.ALERTS_S3_OBJECT_KEY_PREFIX,
                ),
            ],
        )

        s3_to_grafana_lambda.add_event_source(dashboard_s3_event_source)
        s3_to_grafana_lambda.add_event_source(alerts_s3_event_source)
