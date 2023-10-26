# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
import pytest
from aws_cdk import App, Stack
from syrupy.extensions.json import JSONSnapshotExtension
from syrupy.matchers import path_type
from syrupy.types import SerializableData

# Connected Mobility Solution on AWS
from ....config.constants import UserAuthenticationConstants
from ....infrastructure.cms_user_authentication_on_aws_stack import (
    CmsUserAuthenticationOnAwsStack,
)
from ....infrastructure.constructs.app_client_lambda import AppClientLambdaConstruct
from ....infrastructure.constructs.app_registry import AppRegistryConstruct
from ....infrastructure.constructs.cognito import CognitoConstruct
from ....infrastructure.constructs.custom_resource_lambda import (
    CustomResourceLambdaConstruct,
)
from ....infrastructure.constructs.lambda_dependencies import (
    LambdaDependenciesConstruct,
)
from ....infrastructure.constructs.module_integration import ModuleOutputsConstruct
from ....infrastructure.constructs.token_exchange_lambda import (
    TokenExchangeLambdaConstruct,
)
from ....infrastructure.constructs.token_validation_lambda import (
    TokenValidationLambdaConstruct,
)
from ....infrastructure.lib.user_pool_client_actions_enum import UserPoolClientActions


@pytest.fixture(name="snapshot_json_with_matcher")
def fixture_snapshot_json_with_matcher(snapshot: SerializableData) -> SerializableData:
    matcher = path_type(
        mapping={"^(.*)\\.S3Key$": (str,), "^(.*)\\.TemplateURL\\.(.*)$": (list,)},
        regex=True,
    )
    return snapshot.use_extension(JSONSnapshotExtension)(matcher=matcher)


@pytest.fixture(name="cms_user_authentication_on_aws_stack", scope="package")
def fixture_stack() -> CmsUserAuthenticationOnAwsStack:
    app = App()
    cms_user_authentication_on_aws_stack = CmsUserAuthenticationOnAwsStack(
        app, "cms-user-authentication-on-aws-test"
    )
    return cms_user_authentication_on_aws_stack


@pytest.fixture(name="app_registry_stack", scope="package")
def fixture_app_registry_stack() -> Stack:
    app_registry_stack = Stack()
    AppRegistryConstruct(
        app_registry_stack,
        "cms-user-authentication-app-registry-test",
        application_name=UserAuthenticationConstants.APP_NAME,
        application_type=UserAuthenticationConstants.APPLICATION_TYPE,
        solution_id=UserAuthenticationConstants.SOLUTION_ID,
        solution_name=UserAuthenticationConstants.SOLUTION_NAME,
        solution_version=UserAuthenticationConstants.SOLUTION_VERSION,
    )
    return app_registry_stack


@pytest.fixture(name="lambda_dependencies_stack", scope="package")
def fixture_lambda_dependencies_stack() -> Stack:
    lambda_dependencies_stack = Stack()
    LambdaDependenciesConstruct(
        lambda_dependencies_stack,
        "cms-token-exchange-lambda-dependencies-test",
        dependency_layer_dir_name="user_authentication_dependency_layer",
    )
    return lambda_dependencies_stack


@pytest.fixture(name="token_exchange_lambda_stack", scope="package")
def fixture_token_exchange_lambda_stack() -> Stack:
    token_exchange_lambda_stack = Stack()
    dependency_layer_construct = LambdaDependenciesConstruct(
        token_exchange_lambda_stack,
        "cms-token-exchange-lambda-dependencies-test",
        dependency_layer_dir_name="user_authentication_dependency_layer",
    )
    TokenExchangeLambdaConstruct(  # nosec
        token_exchange_lambda_stack,
        "cms-token-exchange-lambda-test",
        dependency_layer=dependency_layer_construct.dependency_layer,
        user_client_id="test-client-id",
        user_client_secret_arn="test_token_validation_lambda_arn",
        domain_prefix="test-domain-prefix",
        redirect_uri="https://localhost",
        user_pool_region="us-west-2",
        token_validation_lambda_arn="test_token_validation_lambda_arn",
    )
    return token_exchange_lambda_stack


@pytest.fixture(name="token_validation_lambda_stack", scope="package")
def fixture_token_validation_lambda_stack() -> Stack:
    token_validation_lambda_stack = Stack()
    dependency_layer_construct = LambdaDependenciesConstruct(
        token_validation_lambda_stack,
        "cms-user-token-validation-lambda-dependencies-test",
        dependency_layer_dir_name="user_authentication_dependency_layer",
    )
    TokenValidationLambdaConstruct(
        token_validation_lambda_stack,
        "cms-token-validation-lambda-test",
        dependency_layer=dependency_layer_construct.dependency_layer,
        user_client_id="test-user-client_id",
        user_pool_id="test-user-pool-id",
        service_client_id="test-service-client-id",
        formatted_cms_service_scope="test-cms-resource-server/test-cms-scope-name",
    )
    return token_validation_lambda_stack


@pytest.fixture(name="module_integration_stack", scope="package")
def fixture_module_integration_stack() -> Stack:
    module_integration_stack = Stack()
    ModuleOutputsConstruct(  # nosec
        module_integration_stack,
        "cms-user-authentication-module-outputs-test",
        user_pool_region="us-west-2",
        user_pool_domain_prefix="test-domain-prefix",
        service_client_id="test-service-client-id",
        secretsmanager_service_client_secret_arn="test-service-client-secret-arn",
        service_caller_scope_name="test_service_caller_scope_name",
        resource_server_identifier="test-resource-server-identifier",
        create_app_client_lambda_function_arn="test_create_app_client_lambda_arn",
        update_app_client_lambda_function_arn="test_update_app_client_lambda_arn",
        delete_app_client_lambda_function_arn="test_delete_app_client_lambda_arn",
        token_exchange_lambda_arn="test_user_authentication_lambda_arn",
        token_validation_lambda_arn="test_token_validation_lambda_arn",
    )
    return module_integration_stack


@pytest.fixture(name="app_client_lambda_stack", scope="package")
def fixture_app_client_lambda_stack() -> Stack:
    app_client_lambda_stack = Stack()
    lambda_dependency_construct = LambdaDependenciesConstruct(
        app_client_lambda_stack,
        "cms-token-exchange-lambda-dependencies-test",
        dependency_layer_dir_name="user_authentication_dependency_layer",
    )
    AppClientLambdaConstruct(
        app_client_lambda_stack,
        "cms-user-authentication-app-client-lambda-test",
        dependency_layer=lambda_dependency_construct.dependency_layer,
        cognito_user_pool_arn="test-user-pool-arn",
        cognito_user_pool_id="test-user-pool-id",
        handler="test_handler_route",
        function_name="test_function_name",
        action=UserPoolClientActions.CREATE.value,
    )
    return app_client_lambda_stack


@pytest.fixture(name="custom_resource_lambda_stack", scope="package")
def fixture_custom_resource_lambda_stack() -> Stack:
    custom_resource_lambda_stack = Stack()
    lambda_dependency_construct = LambdaDependenciesConstruct(
        custom_resource_lambda_stack,
        "cms-token-exchange-lambda-dependencies-test",
        dependency_layer_dir_name="user_authentication_dependency_layer",
    )
    CustomResourceLambdaConstruct(
        custom_resource_lambda_stack,
        "cms-user-authentication-custom-resource-lambda-test",
        dependency_layer=lambda_dependency_construct.dependency_layer,
    )
    return custom_resource_lambda_stack


@pytest.fixture(name="cognito_stack", scope="package")
def fixture_cognito_stack() -> Stack:
    cognito_user_pool_stack = Stack()
    lambda_dependency_construct = LambdaDependenciesConstruct(
        cognito_user_pool_stack,
        "cms-token-exchange-lambda-dependencies-test",
        dependency_layer_dir_name="user_authentication_dependency_layer",
    )
    custom_resource_lambda_construct = CustomResourceLambdaConstruct(
        cognito_user_pool_stack,
        "cms-user-authentication-custom-resource-lambda-test",
        dependency_layer=lambda_dependency_construct.dependency_layer,
    )
    CognitoConstruct(
        cognito_user_pool_stack,
        "cms-user-authentication-cognito-user-pool-test",
        custom_resource_lambda_construct=custom_resource_lambda_construct,
    )
    return cognito_user_pool_stack
