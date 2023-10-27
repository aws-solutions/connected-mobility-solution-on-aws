# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
from typing import Any, Dict, Generator

# Third Party Libraries
import pytest
from mypy_boto3_secretsmanager.type_defs import CreateSecretResponseTypeDef


@pytest.fixture(name="vehicle_trigger_alarm_event")
def fixture_vehicle_trigger_alarm_event(
    service_client_credentials_secret: CreateSecretResponseTypeDef,
) -> Generator[Dict[str, Any], None, None]:
    os.environ.update(
        {
            "ALERTS_PUBLISH_ENDPOINT_URL": "https://test-alert-url.com",
            "AUTHENTICATION_USER_POOL_REGION": "us-east-1",
            "AUTHENTICATION_USER_POOL_DOMAIN": "test-user-pool-domain.com",
            "AUTHENTICATION_SERVICE_CLIENT_ID": "test-client-id",
            "AUTHENTICATION_SERVICE_CLIENT_SECRET_ARN": service_client_credentials_secret[
                "ARN"
            ],
            "AUTHENTICATION_SERVICE_CALLER_SCOPE": "test-caller-scope",
            "AUTHENTICATION_RESOURCE_SERVER_ID": "test-resource-server",
            "USER_AGENT_STRING": "test-user-agent",
        }
    )
    yield {
        "vin": "test-vin",
        "message": "test-message",
    }
