# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any

# Third Party Libraries
from aws_cdk import Stack, Tags, aws_ssm
from constructs import Construct

# Connected Mobility Solution on AWS
from ..config.constants import UserAuthenticationConstants
from .constructs.app_client_lambda import AppClientLambdaConstruct
from .constructs.app_registry import AppRegistryConstruct
from .constructs.cognito import CognitoConstruct
from .constructs.custom_resource_lambda import CustomResourceLambdaConstruct
from .constructs.lambda_dependencies import LambdaDependenciesConstruct
from .constructs.module_integration import ModuleOutputsConstruct
from .constructs.token_exchange_lambda import TokenExchangeLambdaConstruct
from .constructs.token_validation_lambda import TokenValidationLambdaConstruct
from .lib.user_pool_client_actions_enum import UserPoolClientActions


class CmsUserAuthenticationOnAwsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        deployment_uuid = aws_ssm.StringParameter.from_string_parameter_name(
            self,
            "deployment-uuid",
            f"/{UserAuthenticationConstants.STAGE}/cms/common/config/deployment-uuid",
        ).string_value

        user_authentication_construct = CmsUserAuthenticationConstruct(
            self, "cms-user-authentication"
        )

        Tags.of(user_authentication_construct).add(
            "Solutions:DeploymentUUID", deployment_uuid
        )


class CmsUserAuthenticationConstruct(Construct):
    def __init__(self, scope: Construct, construct_id: str) -> None:
        super().__init__(scope, construct_id)

        self.app_registry_construct = AppRegistryConstruct(
            self,
            "app-registry",
            application_name=UserAuthenticationConstants.APP_NAME,
            application_type=UserAuthenticationConstants.APPLICATION_TYPE,
            solution_id=UserAuthenticationConstants.SOLUTION_ID,
            solution_name=UserAuthenticationConstants.SOLUTION_NAME,
            solution_version=UserAuthenticationConstants.SOLUTION_VERSION,
        )

        lambda_dependencies_construct = LambdaDependenciesConstruct(
            self,
            "lambda-dependencies",
            dependency_layer_dir_name="user_authentication_dependency_layer",
        )

        custom_resource_lambda_construct = CustomResourceLambdaConstruct(
            self,
            "custom-resource-lambda",
            dependency_layer=lambda_dependencies_construct.dependency_layer,
        )

        cognito_construct = CognitoConstruct(
            self,
            "cognito",
            custom_resource_lambda_construct=custom_resource_lambda_construct,
        )

        create_app_client_lambda_construct = AppClientLambdaConstruct(
            self,
            "create-app-client-lambda",
            function_name=f"{UserAuthenticationConstants.APP_NAME}-create-app-client",
            action=UserPoolClientActions.CREATE.value,
            handler="create_app_client_lambda.main.handler",
            dependency_layer=lambda_dependencies_construct.dependency_layer,
            cognito_user_pool_id=cognito_construct.user_pool.user_pool_id,
            cognito_user_pool_arn=cognito_construct.user_pool.user_pool_arn,
        )

        update_app_client_lambda_construct = AppClientLambdaConstruct(
            self,
            "update-app-client-lambda",
            function_name=f"{UserAuthenticationConstants.APP_NAME}-update-app-client",
            action=UserPoolClientActions.UPDATE.value,
            handler="update_app_client_lambda.main.handler",
            dependency_layer=lambda_dependencies_construct.dependency_layer,
            cognito_user_pool_id=cognito_construct.user_pool.user_pool_id,
            cognito_user_pool_arn=cognito_construct.user_pool.user_pool_arn,
        )

        delete_app_client_lambda_construct = AppClientLambdaConstruct(
            self,
            "delete-app-client-lambda",
            function_name=f"{UserAuthenticationConstants.APP_NAME}-delete-app-client",
            action=UserPoolClientActions.DELETE.value,
            handler="delete_app_client_lambda.main.handler",
            dependency_layer=lambda_dependencies_construct.dependency_layer,
            cognito_user_pool_id=cognito_construct.user_pool.user_pool_id,
            cognito_user_pool_arn=cognito_construct.user_pool.user_pool_arn,
        )

        # The scope included in the access_token from a CMS service is of the format: "<resource-server-id>/<service-scope-name>"
        formatted_cms_service_scope = f"{cognito_construct.resource_server.user_pool_resource_server_id}/{cognito_construct.service_caller_scope.scope_name}"
        token_validation_lambda_construct = TokenValidationLambdaConstruct(
            self,
            "token-validation-lambda",
            dependency_layer=lambda_dependencies_construct.dependency_layer,
            user_pool_id=cognito_construct.user_pool.user_pool_id,
            user_client_id=cognito_construct.user_app_client.user_pool_client_id,
            service_client_id=cognito_construct.service_app_client.user_pool_client_id,
            formatted_cms_service_scope=formatted_cms_service_scope,
        )

        token_exchange_lambda_construct = TokenExchangeLambdaConstruct(
            self,
            "token-exchange-lambda",
            dependency_layer=lambda_dependencies_construct.dependency_layer,
            user_client_id=cognito_construct.user_app_client.user_pool_client_id,
            user_client_secret_arn=cognito_construct.secretsmanager_user_client_secret.secret_arn,
            redirect_uri="https://localhost",
            domain_prefix=cognito_construct.domain_prefix,
            user_pool_region=Stack.of(self).region,
            token_validation_lambda_arn=token_validation_lambda_construct.lambda_function.function_arn,
        )

        ModuleOutputsConstruct(
            self,
            "module-outputs",
            user_pool_region=Stack.of(self).region,
            user_pool_domain_prefix=cognito_construct.domain_prefix,
            service_client_id=cognito_construct.service_app_client.user_pool_client_id,
            secretsmanager_service_client_secret_arn=cognito_construct.secretsmanager_service_client_secret.secret_arn,
            service_caller_scope_name=cognito_construct.service_caller_scope.scope_name,
            resource_server_identifier=cognito_construct.resource_server.user_pool_resource_server_id,
            create_app_client_lambda_function_arn=create_app_client_lambda_construct.lambda_function.function_arn,
            update_app_client_lambda_function_arn=update_app_client_lambda_construct.lambda_function.function_arn,
            delete_app_client_lambda_function_arn=delete_app_client_lambda_construct.lambda_function.function_arn,
            token_exchange_lambda_arn=token_exchange_lambda_construct.lambda_function.function_arn,
            token_validation_lambda_arn=token_validation_lambda_construct.lambda_function.function_arn,
        )
