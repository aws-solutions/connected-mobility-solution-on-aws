# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
import pytest

# Connected Mobility Solution on AWS
from ..stack_inputs import SolutionConfigInputs


@pytest.fixture(name="solution_config")
def fixture_solution_config() -> SolutionConfigInputs:
    return SolutionConfigInputs(
        solution_id="test-solution-id",
        solution_name="test-solution-name",
        solution_version="test-solution-version",
        module_name="test-module-name",
        module_short_name="test-module-short-name",
        capability_id="test-capability-id",
        application_type="test-application-type",
    )
