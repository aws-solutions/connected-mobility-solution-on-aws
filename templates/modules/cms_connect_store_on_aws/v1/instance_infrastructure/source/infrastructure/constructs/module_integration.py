# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from dataclasses import dataclass
from typing import Any

# Third Party Libraries
from aws_cdk import aws_ssm
from constructs import Construct

# Connected Mobility Solution on AWS
from ...config.constants import ConnectStoreConstants


@dataclass(frozen=True)
class ServiceAuthenticationParameters:
    user_pool_domain: str
    user_pool_region: str
    client_id: str
    client_secret_arn: str
    caller_scope: str
    resource_server_id: str


class ModuleInputsConstruct(Construct):
    def __init__(self, scope: Construct, construct_id: str, **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)
        authentication_service_client_id = aws_ssm.StringParameter.from_string_parameter_attributes(
            self,
            "ssm-authentication-service-client-id",
            parameter_name=f"/{ConnectStoreConstants.STAGE}/cms/authentication/service-client/id",
        )

        authentication_service_client_secret_arn = aws_ssm.StringParameter.from_string_parameter_attributes(
            self,
            "ssm-authentication-service-client-secret-arn",
            parameter_name=f"/{ConnectStoreConstants.STAGE}/cms/authentication/service-client-secret/secret-arn",
        )

        authentication_user_pool_domain = aws_ssm.StringParameter.from_string_parameter_attributes(
            self,
            "ssm-authentication-user-pool-domain",
            parameter_name=f"/{ConnectStoreConstants.STAGE}/cms/authentication/user-pool/domain-prefix",
        )

        authentication_user_pool_region = aws_ssm.StringParameter.from_string_parameter_attributes(
            self,
            "ssm-authentication-user-pool-region",
            parameter_name=f"/{ConnectStoreConstants.STAGE}/cms/authentication/user-pool/region",
        )

        authentication_resource_server_id = aws_ssm.StringParameter.from_string_parameter_attributes(
            self,
            "ssm-authentication-resource-server-id",
            parameter_name=f"/{ConnectStoreConstants.STAGE}/cms/authentication/resource-server/identifier",
        )

        authentication_service_caller_scope = aws_ssm.StringParameter.from_string_parameter_attributes(
            self,
            "ssm-authentication-service-caller-scope",
            parameter_name=f"/{ConnectStoreConstants.STAGE}/cms/authentication/service-caller-scope/name",
        )

        self.service_authentication_parameters = ServiceAuthenticationParameters(
            user_pool_domain=authentication_user_pool_domain.string_value,
            user_pool_region=authentication_user_pool_region.string_value,
            client_id=authentication_service_client_id.string_value,
            client_secret_arn=authentication_service_client_secret_arn.string_value,
            caller_scope=authentication_service_caller_scope.string_value,
            resource_server_id=authentication_resource_server_id.string_value,
        )

        self.alerts_publish_endpoint_url = aws_ssm.StringParameter.from_string_parameter_attributes(
            self,
            "ssm-alerts-publish-endpoint-url",
            parameter_name=f"/{ConnectStoreConstants.STAGE}/cms/alerts/publish-api/endpoint",
        )
