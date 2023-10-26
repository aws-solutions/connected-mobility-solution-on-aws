# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any, Dict

# Third Party Libraries
import pytest


@pytest.fixture(name="create_app_client_lambda_event")
def fixture_create_app_client_lambda_event() -> Dict[str, Any]:
    return {
        "CreateCognitoUserPoolAppClientInput": {
            "ClientName": "TestAppClientName",
            "CallbackURLs": ["TestCallbackURL"],
            "AccessTokenValidityMinutes": 60,
            "IdTokenValidityMinutes": 60,
            "RefreshTokenValidityMinutes": 60,
        }
    }
