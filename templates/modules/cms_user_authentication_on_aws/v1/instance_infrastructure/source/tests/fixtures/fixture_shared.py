# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os

# Third Party Libraries
import pytest


# Prevents boto from accidentally using default AWS credentials if not mocked
@pytest.fixture(scope="session", autouse=True)
def fixture_aws_credentials() -> None:
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"  # nosec
    os.environ["AWS_SECRET_ACCESS_ID"] = "testing"  # nosec
    os.environ["AWS_SECURITY_TOKEN"] = "testing"  # nosec
    os.environ["AWS_SESSION_TOKEN"] = "testing"  # nosec
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"  # nosec
