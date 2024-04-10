# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
from os.path import abspath, dirname
from typing import Any

# AWS Libraries
from aws_cdk import Aws, CfnMapping, Stack, Tags
from constructs import Construct

# CMS Common Library
from cms_common.config.ssm import get_resolvable_ssm_deployment_uuid
from cms_common.config.stack_inputs import S3AssetConfigInputs, SolutionConfigInputs
from cms_common.constructs.app_registry import AppRegistryConstruct, AppRegistryInputs
from cms_common.constructs.app_unique_id import AppUniqueId
from cms_common.constructs.cdk_lambda_vpc_config_construct import (
    CDKLambdasVpcConfigConstruct,
)
from cms_common.constructs.lambda_dependencies import LambdaDependenciesConstruct
from cms_common.constructs.vpc_construct import VpcConstruct

# Connected Mobility Solution on AWS
from .constructs.appsync_frontend_api import FrontendApisConstruct
from .constructs.authorization_lambda import AuthorizationLambdaConstruct
from .constructs.incoming_alerts_construct import IncomingAlertsConstruct
from .constructs.module_integration import ModuleInputsConstruct, ModuleOutputsConstruct
from .constructs.notification_construct import NotificationConstruct
from .constructs.publish_api import PublishApiConstruct
from .constructs.sns_to_sqs_construct import SnsToSqsToLambdaConstruct
from .constructs.user_subscriptions_construct import UserSubscriptionsConstruct


class CmsAlertsStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        solution_config_inputs: SolutionConfigInputs,
        s3_asset_config_inputs: S3AssetConfigInputs,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        CfnMapping(
            self,
            "Solution",
            mapping={
                "AssetsConfig": {
                    "S3AssetBucketBaseName": s3_asset_config_inputs.bucket_base_name,
                    "S3AssetKeyPrefix": s3_asset_config_inputs.object_key_prefix,
                },
            },
        )

        self.module_inputs_construct = ModuleInputsConstruct(
            self, "module-inputs-construct"
        )
        app_unique_id = self.module_inputs_construct.app_unique_id

        # Check if a config stack for the app unique id is registered. Fail stack
        # creation if it is not registered. If config stack exists, then create an SSM
        # parameter to register the module with the app unique id.
        register_module_with_app_unique_id = AppUniqueId.register_module(
            self,
            app_unique_id=app_unique_id,
            module_name=solution_config_inputs.module_short_name,
        )

        deployment_uuid = get_resolvable_ssm_deployment_uuid(
            app_unique_id=app_unique_id
        )

        self.alerts_construct = CmsAlertsConstruct(
            self,
            "cms-alerts",
            deployment_uuid=deployment_uuid,
            solution_config_inputs=solution_config_inputs,
            module_inputs_construct=self.module_inputs_construct,
        )
        self.alerts_construct.node.add_dependency(register_module_with_app_unique_id)

        Tags.of(self.alerts_construct).add("Solutions:DeploymentUUID", deployment_uuid)


class CmsAlertsConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        deployment_uuid: str,
        solution_config_inputs: SolutionConfigInputs,
        module_inputs_construct: ModuleInputsConstruct,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        AppRegistryConstruct(
            self,
            "app-registry",
            app_registry_inputs=AppRegistryInputs(
                application_name=Aws.STACK_NAME,
                application_type=solution_config_inputs.application_type,
                solution_id=solution_config_inputs.solution_id,
                solution_name=solution_config_inputs.solution_name,
                solution_version=solution_config_inputs.solution_version,
            ),
        )

        vpc_construct = VpcConstruct(
            self, "vpc-construct", vpc_config=module_inputs_construct.vpc_config
        )

        self.cdk_lambda_vpc_config_construct = CDKLambdasVpcConfigConstruct(
            self,
            "cdk-lambdas-vpc-config-construct",
            vpc_construct=vpc_construct,
            subnets=module_inputs_construct.vpc_config.private_subnets,
        )

        lambda_dependencies_construct = LambdaDependenciesConstruct(
            self,
            "dependency-layer",
            pipfile_path=f"{dirname(dirname(dirname(abspath(__file__))))}/Pipfile",
            dependency_layer_path=f"{os.getcwd()}/source/infrastructure/cms_alerts_dependency_layer",
        )

        authorization_construct = AuthorizationLambdaConstruct(  # nosec
            self,
            "auth-construct",
            app_unique_id=module_inputs_construct.app_unique_id,
            solution_config_inputs=solution_config_inputs,
            dependency_layer=lambda_dependencies_construct.dependency_layer,
            token_validation_lambda_arn=module_inputs_construct.token_validation_lambda_arn,
            vpc_construct=vpc_construct,
        )

        user_subscriptions_construct = UserSubscriptionsConstruct(
            self,
            "user-subscriptions-construct",
            app_unique_id=module_inputs_construct.app_unique_id,
            solution_config_inputs=solution_config_inputs,
            dependency_layer=lambda_dependencies_construct.dependency_layer,
            deployment_uuid=deployment_uuid,
            sns_topic_prefix=module_inputs_construct.sns_topic_prefix,
            vpc_construct=vpc_construct,
        )

        notification_construct = NotificationConstruct(
            self,
            "notification-construct",
            app_unique_id=module_inputs_construct.app_unique_id,
            solution_config_inputs=solution_config_inputs,
            dependency_layer=lambda_dependencies_construct.dependency_layer,
            deployment_uuid=deployment_uuid,
            user_subscription_topic_general_key_id=user_subscriptions_construct.user_subscription_topic_general_key.key_id,
            sns_topic_prefix=module_inputs_construct.sns_topic_prefix,
            vpc_construct=vpc_construct,
        )

        incoming_alerts_construct = IncomingAlertsConstruct(
            self,
            "incoming-alerts-construct",
            app_unique_id=module_inputs_construct.app_unique_id,
            solution_config_inputs=solution_config_inputs,
            dependency_layer=lambda_dependencies_construct.dependency_layer,
            notifications_table_name=notification_construct.notifications_table.table_name,
            notifications_table_key_id=notification_construct.notifications_table_key.key_id,
            sns_topic_prefix=module_inputs_construct.sns_topic_prefix,
            vpc_construct=vpc_construct,
        )

        sns_to_sqs_construct = SnsToSqsToLambdaConstruct(
            self,
            "sns-to-sqs-construct",
            app_unique_id=module_inputs_construct.app_unique_id,
            solution_config_inputs=solution_config_inputs,
            incoming_alerts_construct=incoming_alerts_construct,
        )

        frontend_api_construct = FrontendApisConstruct(
            self,
            "frontend-api-construct",
            app_unique_id=module_inputs_construct.app_unique_id,
            solution_config_inputs=solution_config_inputs,
            user_subscriptions_lambda=user_subscriptions_construct.user_subscriptions_lambda,
            authorization_lambda=authorization_construct.authorization_lambda,
        )

        publish_api_construct = PublishApiConstruct(
            self,
            "publish-api-construct",
            app_unique_id=module_inputs_construct.app_unique_id,
            solution_config_inputs=solution_config_inputs,
            authorization_lambda=authorization_construct.authorization_lambda,
            dependency_layer=lambda_dependencies_construct.dependency_layer,
            sns_topic_arn=sns_to_sqs_construct.sns_topic.topic_arn,
            sns_topic_key_id=sns_to_sqs_construct.sns_topic_key.key_id,
            vpc_construct=vpc_construct,
        )

        ModuleOutputsConstruct(
            self,
            "module-outputs",
            app_unique_id=module_inputs_construct.app_unique_id,
            solution_config_inputs=solution_config_inputs,
            publish_api_endpoint=publish_api_construct.graphql_api.graphql_url,
            frontend_api_endpoint=frontend_api_construct.graphql_api.graphql_url,
        )
