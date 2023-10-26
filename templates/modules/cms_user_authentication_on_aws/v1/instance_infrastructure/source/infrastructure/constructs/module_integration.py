# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
from aws_cdk import aws_ssm
from constructs import Construct

# Connected Mobility Solution on AWS
from ...config.constants import UserAuthenticationConstants


class ModuleOutputsConstruct(Construct):
    def __init__(  # pylint: disable=too-many-arguments
        self,
        scope: Construct,
        construct_id: str,
        user_pool_region: str,
        user_pool_domain_prefix: str,
        service_client_id: str,
        secretsmanager_service_client_secret_arn: str,
        service_caller_scope_name: str,
        resource_server_identifier: str,
        create_app_client_lambda_function_arn: str,
        update_app_client_lambda_function_arn: str,
        delete_app_client_lambda_function_arn: str,
        token_exchange_lambda_arn: str,
        token_validation_lambda_arn: str,
    ) -> None:
        super().__init__(scope, construct_id)

        aws_ssm.StringParameter(
            self,
            "ssm-user-pool-region",
            string_value=user_pool_region,
            description="AWS Region of the Cognito UserPool",
            parameter_name=f"/{UserAuthenticationConstants.STAGE}/cms/authentication/user-pool/region",
        )

        aws_ssm.StringParameter(
            self,
            "ssm-user-pool-domain-prefix",
            string_value=user_pool_domain_prefix,
            description="Domain prefix used by the Cognito HostedUI",
            parameter_name=f"/{UserAuthenticationConstants.STAGE}/cms/authentication/user-pool/domain-prefix",
        )

        aws_ssm.StringParameter(
            self,
            "ssm-service-client-id",
            string_value=service_client_id,
            description="App client by services for client credential flow",
            parameter_name=f"/{UserAuthenticationConstants.STAGE}/cms/authentication/service-client/id",
        )

        aws_ssm.StringParameter(
            self,
            "ssm-service-client-secret-arn",
            string_value=secretsmanager_service_client_secret_arn,
            description="App client secret ARN for service client secret.",
            parameter_name=f"/{UserAuthenticationConstants.STAGE}/cms/authentication/service-client-secret/secret-arn",
        )

        aws_ssm.StringParameter(
            self,
            "ssm-service-caller-scope-name",
            string_value=service_caller_scope_name,
            description="Name of the scope to be used by service callers using the client credentials OAuth flow",
            parameter_name=f"/{UserAuthenticationConstants.STAGE}/cms/authentication/service-caller-scope/name",
        )

        aws_ssm.StringParameter(
            self,
            "ssm-resource-server-identifier",
            string_value=resource_server_identifier,
            description="Unique identifier of the Cognito ResourceServer",
            parameter_name=f"/{UserAuthenticationConstants.STAGE}/cms/authentication/resource-server/identifier",
        )

        aws_ssm.StringParameter(
            self,
            "ssm-create-app-client-lambda-arn",
            string_value=create_app_client_lambda_function_arn,
            description="CMS Create App client lambda function ARN",
            parameter_name=f"/{UserAuthenticationConstants.STAGE}/cms/authentication/create-app-client-lambda/arn",
        )

        aws_ssm.StringParameter(
            self,
            "ssm-update-app-client-lambda-arn",
            string_value=update_app_client_lambda_function_arn,
            description="CMS Update App client lambda function ARN",
            parameter_name=f"/{UserAuthenticationConstants.STAGE}/cms/authentication/update-app-client-lambda/arn",
        )

        aws_ssm.StringParameter(
            self,
            "ssm-delete-app-client-lambda-arn",
            string_value=delete_app_client_lambda_function_arn,
            description="CMS Delete App client lambda function ARN",
            parameter_name=f"/{UserAuthenticationConstants.STAGE}/cms/authentication/delete-app-client-lambda/arn",
        )

        aws_ssm.StringParameter(
            self,
            "ssm-user-authentication-lambda-arn",
            string_value=token_exchange_lambda_arn,
            description="Arn for lambda function that authenticates users",
            parameter_name=f"/{UserAuthenticationConstants.STAGE}/cms/authentication/user-authentication-lambda/arn",
        )

        aws_ssm.StringParameter(
            self,
            "ssm-token-validation-lambda-arn",
            string_value=token_validation_lambda_arn,
            description="Arn for lambda function that validates tokens",
            parameter_name=f"/{UserAuthenticationConstants.STAGE}/cms/authentication/token-validation-lambda/arn",
        )
