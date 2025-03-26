# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any, Dict, Generator, List, Optional
from unittest.mock import MagicMock, patch

# Third Party Libraries
import pytest

# AWS Libraries
import botocore
from botocore.stub import Stubber


def boto3_client_selector_side_effect(
    timestream_client: MagicMock,
    ssm_client: MagicMock,
    client_type: str,
    *args: List[Any],  # catch unused args from boto3.client
    return_value: Optional[
        Any
    ] = None,  # injected return_value for unit test purposes, not in boto3.client interface
    **kwargs: Dict[str, Any]  # catch unused kwargs from boto3.client
) -> Any:
    if client_type == "timestream-query":
        selected_client = timestream_client
    elif client_type == "ssm":
        selected_client = ssm_client
    else:
        raise AttributeError("Unsupported boto3 client type specified")

    if return_value is not None:
        selected_client.return_value = return_value

    return selected_client.return_value


@pytest.fixture(name="mock_boto3_client")
def fixture_mock_boto3_client() -> Generator[MagicMock, None, None]:
    timestream_client = MagicMock()
    ssm_client = MagicMock()

    with patch(
        "boto3.client",
        side_effect=lambda *args, **kwargs: boto3_client_selector_side_effect(
            timestream_client, ssm_client, *args, **kwargs
        ),
    ) as client:
        yield client


@pytest.fixture(name="ssm_client_stubber")
def fixture_ssm_stubber() -> Generator[Stubber, None, None]:
    ssm_client = botocore.session.get_session().create_client("ssm")
    with Stubber(ssm_client) as stubber:
        yield stubber


@pytest.fixture(name="timestream_client_stubber")
def fixture_timestream_stubber() -> Generator[Stubber, None, None]:
    timestream_client = botocore.session.get_session().create_client("timestream-query")
    with Stubber(timestream_client) as stubber:
        yield stubber
