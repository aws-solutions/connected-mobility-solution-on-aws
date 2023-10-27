# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any

# Third Party Libraries
from aws_cdk import Stack, Tags, aws_ssm
from constructs import Construct

# Connected Mobility Solution on AWS
from ..config.constants import AlertsConstants
from ..infrastructure.constructs.app_registry import AppRegistryConstruct
from .constructs.appsync_frontend_api import FrontendApisConstruct
from .constructs.authorization_lambda import AuthorizationLambdaConstruct
from .constructs.incoming_alerts_construct import IncomingAlertsConstruct
from .constructs.lambda_dependencies import LambdaDependenciesConstruct
from .constructs.module_integration import ModuleInputsConstruct, ModuleOutputsConstruct
from .constructs.notification_construct import NotificationConstruct
from .constructs.publish_api import PublishApiConstruct
from .constructs.sns_to_sqs_construct import SnsToSqsToLambdaConstruct
from .constructs.user_subscriptions_construct import UserSubscriptionsConstruct


class CmsAlertsOnAwsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)
        deployment_uuid = aws_ssm.StringParameter.from_string_parameter_name(
            self,
            "deployment-uuid",
            f"/{AlertsConstants.STAGE}/cms/common/config/deployment-uuid",
        ).string_value

        alerts_construct = CmsAlertsConstruct(self, "cms-alerts", deployment_uuid)

        Tags.of(alerts_construct).add("Solutions:DeploymentUUID", deployment_uuid)


class CmsAlertsConstruct(Construct):
    def __init__(
        self, scope: Construct, construct_id: str, deployment_uuid: str, **kwargs: Any
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        AppRegistryConstruct(
            self,
            "cms-alerts-app-registry",
            application_name=AlertsConstants.APP_NAME,
            application_type=AlertsConstants.APPLICATION_TYPE,
            solution_id=AlertsConstants.SOLUTION_ID,
            solution_name=AlertsConstants.SOLUTION_NAME,
            solution_version=AlertsConstants.SOLUTION_VERSION,
        )

        self.module_inputs_construct = ModuleInputsConstruct(
            self, "module-inputs-construct"
        )

        self.dependency_layer_construct = LambdaDependenciesConstruct(
            self,
            "alerts-lambda-dependencies",
            dependency_layer_dir_name="alerts_dependency_layer",
        )

        self.authorization_construct = AuthorizationLambdaConstruct(  # nosec
            self,
            "auth-construct",
            dependency_layer=self.dependency_layer_construct.dependency_layer,
            token_validation_lambda_arn=self.module_inputs_construct.token_validation_lambda_arn.string_value,
            token_use="access",
        )

        self.user_subscriptions_construct = UserSubscriptionsConstruct(
            self,
            "user-subscriptions-construct",
            dependency_layer=self.dependency_layer_construct.dependency_layer,
            deployment_uuid=deployment_uuid,
        )

        self.notification_construct = NotificationConstruct(
            self,
            "notification-construct",
            self.dependency_layer_construct.dependency_layer,
            deployment_uuid=deployment_uuid,
            user_subscription_topic_general_key_id=self.user_subscriptions_construct.user_subscription_topic_general_key.key_id,
        )

        self.incoming_alerts_construct = IncomingAlertsConstruct(
            self,
            "incoming-alerts-construct",
            dependency_layer=self.dependency_layer_construct.dependency_layer,
            notifications_table_name=self.notification_construct.notifications_table.table_name,
            notifications_table_key_id=self.notification_construct.notifications_table_key.key_id,
        )

        self.sns_to_sqs_construct = SnsToSqsToLambdaConstruct(
            self,
            "sns-to-sqs-construct",
            incoming_alerts_construct=self.incoming_alerts_construct,
        )

        self.frontend_api_construct = FrontendApisConstruct(
            self,
            "frontend-api-construct",
            user_subscriptions_lambda=self.user_subscriptions_construct.user_subscriptions_lambda,
            authorization_lambda=self.authorization_construct.authorization_lambda,
        )

        self.publish_api_construct = PublishApiConstruct(
            self,
            "publish-api-construct",
            authorization_lambda=self.authorization_construct.authorization_lambda,
            dependency_layer=self.dependency_layer_construct.dependency_layer,
            sns_topic_arn=self.sns_to_sqs_construct.sns_topic.topic_arn,
            sns_topic_key_id=self.sns_to_sqs_construct.sns_topic_key.key_id,
        )

        ModuleOutputsConstruct(
            self,
            "module-outputs",
            publish_api_endpoint=self.publish_api_construct.graphql_api.graphql_url,
            frontend_api_endpoint=self.frontend_api_construct.graphql_api.graphql_url,
        )
