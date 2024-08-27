# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Callable, Dict, List, Tuple

# Third Party Libraries
import pytest
from moto import mock_aws

# Connected Mobility Solution on AWS
from ..auth_configs import (
    AuthConfigError,
    CMSClientConfig,
    CMSIdPConfig,
    get_idp_config,
    get_service_client_config,
    get_user_client_config,
)
from .fixture_auth import TEST_IDENTITY_PROVIDER_ID, TEST_USER_AGENT_STRING


@mock_aws
def test_get_idp_config_success(
    idp_config_secret_string_valid: Dict[str, str | List[str]],
    mock_idp_config_valid: Callable[[], None],
) -> None:
    mock_idp_config_valid()
    idp_config = get_idp_config(TEST_USER_AGENT_STRING, TEST_IDENTITY_PROVIDER_ID)
    assert isinstance(idp_config, CMSIdPConfig)
    assert idp_config.issuer == idp_config_secret_string_valid["issuer"]
    assert idp_config.token_endpoint == idp_config_secret_string_valid["token_endpoint"]
    assert (
        idp_config.authorization_endpoint
        == idp_config_secret_string_valid["authorization_endpoint"]
    )
    assert (
        idp_config.alternate_aud_key
        == idp_config_secret_string_valid["alternate_aud_key"]
    )
    assert idp_config.auds == idp_config_secret_string_valid["auds"]
    assert idp_config.scopes == idp_config_secret_string_valid["scopes"]


def test_get_idp_config_client_error() -> None:
    with pytest.raises(
        AuthConfigError,
        match=r"Auth Config Error: client error while retrieving the secret or ssm parameter from the AWS account.",
    ):
        get_idp_config(TEST_USER_AGENT_STRING, TEST_IDENTITY_PROVIDER_ID)


@mock_aws
def test_get_idp_config_json_decode_error(
    mock_idp_config_invalid_json: Callable[[], None],
) -> None:
    mock_idp_config_invalid_json()
    with pytest.raises(
        AuthConfigError,
        match=r"Auth Config Error: JSON error while decoding the auth config secret.",
    ):
        get_idp_config(
            TEST_USER_AGENT_STRING,
            TEST_IDENTITY_PROVIDER_ID,
        )


@mock_aws
def test_get_idp_config_class_validation_error(
    mock_idp_config_invalid_data_format: Callable[[], None],
) -> None:
    mock_idp_config_invalid_data_format()
    with pytest.raises(
        AuthConfigError,
        match=r"Auth Config Error: error while converting the auth config into the expected data format. Ensure your secret value matches the expected format.",
    ):
        get_idp_config(
            TEST_USER_AGENT_STRING,
            TEST_IDENTITY_PROVIDER_ID,
        )


@mock_aws
def test_get_service_client_config_success(
    service_client_config_secret_string_valid: dict[str, str | Tuple[str, ...]],
    mock_service_client_config_valid: Callable[[], None],
) -> None:
    mock_service_client_config_valid()
    client_config = get_service_client_config(
        TEST_USER_AGENT_STRING, TEST_IDENTITY_PROVIDER_ID
    )
    assert isinstance(client_config, CMSClientConfig)
    assert (
        client_config.audience == service_client_config_secret_string_valid["audience"]
    )
    assert (
        client_config.client_id
        == service_client_config_secret_string_valid["client_id"]
    )
    assert (
        client_config.client_secret
        == service_client_config_secret_string_valid["client_secret"]
    )


@mock_aws
def test_get_user_client_config_success(
    user_client_config_secret_string_valid: dict[str, str | Tuple[str, ...]],
    mock_user_client_config_valid: Callable[[], None],
) -> None:
    mock_user_client_config_valid()
    user_client_config = get_user_client_config(
        TEST_USER_AGENT_STRING, TEST_IDENTITY_PROVIDER_ID
    )
    assert isinstance(user_client_config, CMSClientConfig)
    assert (
        user_client_config.client_id
        == user_client_config_secret_string_valid["client_id"]
    )
    assert (
        user_client_config.client_secret
        == user_client_config_secret_string_valid["client_secret"]
    )
