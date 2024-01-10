# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0


# Standard Library
# mypy: disable-error-code=misc
from typing import Any, Dict
from unittest.mock import patch

# Third Party Libraries
import pytest
from aws_lambda_powertools.utilities.typing import LambdaContext

# Connected Mobility Solution on AWS
from ....handlers.s3_to_grafana.lib.custom_exceptions import GrafanaApiError
from ....handlers.s3_to_grafana.main import handler


def test_s3_to_grafana_dashboard_success(
    grafana_api_key_secret: Dict[str, Any],
    s3_to_grafana_dashboard_event: Dict[str, Any],
    context: LambdaContext,
) -> None:
    with patch("requests.post") as mocked_request_post:
        mocked_request_post.return_value.ok = True
        handler(event=s3_to_grafana_dashboard_event, context=context)


def test_s3_to_grafana_dashboard_fails(
    grafana_api_key_secret: Dict[str, Any],
    s3_to_grafana_dashboard_event: Dict[str, Any],
    context: LambdaContext,
) -> None:
    with patch("requests.post") as mocked_request_post:
        mocked_request_post.return_value.ok = False
        with pytest.raises(GrafanaApiError):
            handler(event=s3_to_grafana_dashboard_event, context=context)


def test_s3_to_grafana_alerts_success(
    grafana_api_key_secret: Dict[str, Any],
    s3_to_grafana_alerts_event: Dict[str, Any],
    context: LambdaContext,
) -> None:
    with patch("requests.post") as mocked_request_post:
        mocked_request_post.return_value.ok = True
        handler(event=s3_to_grafana_alerts_event, context=context)


def test_s3_to_grafana_alerts_fails(
    grafana_api_key_secret: Dict[str, Any],
    s3_to_grafana_alerts_event: Dict[str, Any],
    context: LambdaContext,
) -> None:
    with patch("requests.post") as mocked_request_post:
        mocked_request_post.return_value.ok = False
        mocked_request_post.return_value.status_code = 400
        with pytest.raises(GrafanaApiError):
            handler(event=s3_to_grafana_alerts_event, context=context)
