# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any, Dict

# Third Party Libraries
import pytest


@pytest.fixture(name="update_app_client_lambda_event")
def fixture_update_app_client_lambda_event() -> Dict[str, Any]:
    return {
        "UpdateCognitoUserPoolAppClientInput": {
            "UpdateProperties": {
                "ClientName": "TestAppClientName",
                "CallbackURLs": ["TestCallbackURL"],
            }
        }
    }
