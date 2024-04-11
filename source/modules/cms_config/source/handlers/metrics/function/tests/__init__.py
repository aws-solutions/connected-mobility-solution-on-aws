# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
import unittest


class UnitTestCommon(unittest.TestCase):
    def setUp(self) -> None:
        set_common_env_variables()
        return super().setUp()


def set_common_env_variables() -> None:
    os.environ["SOLUTION_ID"] = "SO0241"
    os.environ["SOLUTION_VERSION"] = "v0.0.0"
    os.environ["AWS_ACCOUNT_ID"] = "0123456789123"
    os.environ["AWS_REGION"] = "us-east-1"
    os.environ["DEPLOYMENT_UUID"] = "DUMMY"
    os.environ["METRICS_SOLUTION_URL"] = "https://localhost"
    os.environ["USER_AGENT_STRING"] = "USER_AGENT"
