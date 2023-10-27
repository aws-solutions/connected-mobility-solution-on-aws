# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library

# Third Party Libraries
from aws_cdk import Duration, Stack, aws_iam, aws_lambda, aws_logs
from constructs import Construct

# Connected Mobility Solution on AWS
from ...config.constants import ConnectStoreConstants
from ..lib.policy_generators import generate_lambda_cloudwatch_logs_policy_document
from .module_integration import ServiceAuthenticationParameters


class AlertsConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        dependency_layer: aws_lambda.LayerVersion,
        alerts_publish_endpoint_url: str,
        service_authentication_parameters: ServiceAuthenticationParameters,
    ) -> None:
        super().__init__(scope, construct_id)

        vehicle_trigger_alarm_lambda_name = (
            f"{ConnectStoreConstants.APP_NAME}-vehicle-alarm"
        )

        vehicle_trigger_alarm_lambda_role = aws_iam.Role(
            self,
            "lambda-role",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),  # NOSONAR
            path="/",
            inline_policies={
                "cloudwatch-logs-policy": generate_lambda_cloudwatch_logs_policy_document(
                    self, lambda_function_name=vehicle_trigger_alarm_lambda_name
                ),
                "secretsmanager-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "secretsmanager:GetSecretValue",
                            ],
                            resources=[
                                service_authentication_parameters.client_secret_arn
                            ],
                        )
                    ]
                ),
            },
        )

        self.vehicle_trigger_alarm_lambda_function = aws_lambda.Function(
            self,
            "lambda-function",
            function_name=vehicle_trigger_alarm_lambda_name,
            code=aws_lambda.Code.from_asset("source/handlers"),
            description="Vehicle Trigger Alarm Function",
            handler="vehicle_trigger_alarm.main.handler",
            runtime=aws_lambda.Runtime.PYTHON_3_10,
            role=vehicle_trigger_alarm_lambda_role,
            layers=[dependency_layer],
            timeout=Duration.minutes(1),
            environment={
                "USER_AGENT_STRING": ConnectStoreConstants.USER_AGENT_STRING,
                "AUTHENTICATION_SERVICE_CLIENT_ID": service_authentication_parameters.client_id,
                "AUTHENTICATION_SERVICE_CLIENT_SECRET_ARN": service_authentication_parameters.client_secret_arn,
                "AUTHENTICATION_SERVICE_CALLER_SCOPE": service_authentication_parameters.caller_scope,
                "AUTHENTICATION_RESOURCE_SERVER_ID": service_authentication_parameters.resource_server_id,
                "AUTHENTICATION_USER_POOL_DOMAIN": service_authentication_parameters.user_pool_domain,
                "AUTHENTICATION_USER_POOL_REGION": service_authentication_parameters.user_pool_region,
                "ALERTS_PUBLISH_ENDPOINT_URL": alerts_publish_endpoint_url,
            },
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
        )

        self.vehicle_trigger_alarm_lambda_function.add_permission(
            id="iot-invoke-vehicle-trigger-alarm-permission",
            principal=aws_iam.ServicePrincipal("iot.amazonaws.com"),  # NOSONAR
            action="lambda:InvokeFunction",
            source_account=Stack.of(self).account,
        )
