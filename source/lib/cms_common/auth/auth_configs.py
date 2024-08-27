# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json
from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING, List, Optional, Union, overload

# Third Party Libraries
from cattrs import ClassValidationError, structure

# AWS Libraries
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

# Connected Mobility Solution on AWS
from ..resource_names.auth import AuthResourceNames

if TYPE_CHECKING:
    # Third Party Libraries
    from mypy_boto3_secretsmanager import SecretsManagerClient
    from mypy_boto3_ssm import SSMClient
else:
    SecretsManagerClient = object
    SSMClient = object


class AuthConfigError(Exception):
    def __init__(
        self,
        message: str = "Could not retrieve or parse auth configurations.",
        code: int = 500,
    ):
        self.message = message
        self.code = code


@dataclass(frozen=True)
class CMSIdPConfig:
    issuer: str
    token_endpoint: str
    authorization_endpoint: str
    auds: List[str]
    scopes: List[str]
    alternate_aud_key: Optional[str] = None

    def __hash__(self) -> int:
        auds_tuple = tuple(sorted(self.auds))
        scopes_tuple = tuple(sorted(self.scopes))
        return hash((self.issuer, self.alternate_aud_key, auds_tuple, scopes_tuple))


@dataclass(frozen=True)
class CMSClientConfig:
    client_id: str
    client_secret: str
    audience: Optional[str] = None


MAX_CACHE_SIZE_BOTO_CLIENT = 10
MAX_CACHE_SIZE_AUTH_CONFIG = 100


@lru_cache(maxsize=MAX_CACHE_SIZE_BOTO_CLIENT)
def _get_secrets_manager_client(user_agent_string: str) -> SecretsManagerClient:
    return boto3.client(
        "secretsmanager",
        config=Config(user_agent_extra=user_agent_string),
    )


@lru_cache(maxsize=MAX_CACHE_SIZE_BOTO_CLIENT)
def _get_ssm_client(user_agent_string: str) -> SSMClient:
    return boto3.client(
        "ssm",
        config=Config(user_agent_extra=user_agent_string),
    )


@lru_cache(maxsize=MAX_CACHE_SIZE_AUTH_CONFIG)
def _get_auth_resource_names(identity_provider_id: str) -> AuthResourceNames:
    return AuthResourceNames.from_identity_provider_id(identity_provider_id)


# Config getter functions
def get_idp_config(
    user_agent_string: str,
    identity_provider_id: str,
) -> CMSIdPConfig:
    auth_resource_names = _get_auth_resource_names(identity_provider_id)
    idp_config_ssm_name = auth_resource_names.idp_config_secret_arn_ssm_parameter
    return _get_config(
        user_agent_string=user_agent_string,
        ssm_name=idp_config_ssm_name,
        config_dataclass_type=CMSIdPConfig,
    )


def get_service_client_config(
    user_agent_string: str,
    identity_provider_id: str,
) -> CMSClientConfig:
    auth_resource_names = _get_auth_resource_names(identity_provider_id)
    client_config_ssm_name = (
        auth_resource_names.service_client_config_secret_arn_ssm_parameter
    )
    return _get_config(
        user_agent_string=user_agent_string,
        ssm_name=client_config_ssm_name,
        config_dataclass_type=CMSClientConfig,
    )


def get_user_client_config(
    user_agent_string: str,
    identity_provider_id: str,
) -> CMSClientConfig:
    auth_resource_names = _get_auth_resource_names(identity_provider_id)
    user_client_config_ssm_name = (
        auth_resource_names.user_client_config_secret_arn_ssm_parameter
    )
    return _get_config(
        user_agent_string=user_agent_string,
        ssm_name=user_client_config_ssm_name,
        config_dataclass_type=CMSClientConfig,
    )


# Overloads necessary for mypy
@overload
def _get_config(
    user_agent_string: str,
    ssm_name: str,
    config_dataclass_type: type[CMSIdPConfig],
) -> CMSIdPConfig:
    ...


@overload
def _get_config(
    user_agent_string: str,
    ssm_name: str,
    config_dataclass_type: type[CMSClientConfig],
) -> CMSClientConfig:
    ...


# Helper function to dynamically get the right config based on SSM path. Each config has an SSM parameter to expose the config secret Arn.
def _get_config(
    user_agent_string: str,
    ssm_name: str,
    config_dataclass_type: Union[type[CMSIdPConfig], type[CMSClientConfig]],
) -> Union[CMSIdPConfig, CMSClientConfig]:
    try:
        config_secret_arn = _get_ssm_client(user_agent_string).get_parameter(
            Name=ssm_name
        )["Parameter"]["Value"]

        config_secret_value = _get_secrets_manager_client(
            user_agent_string
        ).get_secret_value(SecretId=config_secret_arn)["SecretString"]

        config_object = json.loads(config_secret_value)

        try:
            config_dataclass: Union[CMSIdPConfig, CMSClientConfig] = structure(obj=config_object, cl=config_dataclass_type)  # type: ignore[assignment]
        except ClassValidationError as e:
            raise AuthConfigError(
                "Auth Config Error: error while converting the auth config into the expected data format. Ensure your secret value matches the expected format."
            ) from e
    except json.JSONDecodeError as e:
        raise AuthConfigError(
            "Auth Config Error: JSON error while decoding the auth config secret."
        ) from e
    except ClientError as e:
        raise AuthConfigError(
            "Auth Config Error: client error while retrieving the secret or ssm parameter from the AWS account."
        ) from e
    except KeyError as e:
        raise AuthConfigError(
            "Auth Config Error: unexpected response from Secrets Manager get_secret_value. Missing expected 'SecretString' key."
        ) from e
    return config_dataclass
