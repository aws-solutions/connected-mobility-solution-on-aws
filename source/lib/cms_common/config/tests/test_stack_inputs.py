# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Connected Mobility Solution on AWS
from ..stack_inputs import SolutionConfigInputs, create_stack_description


def test_create_stack_description(solution_config: SolutionConfigInputs) -> None:
    assert create_stack_description(solution_config=solution_config) == (
        f"({solution_config.solution_id}-{solution_config.capability_id}) "
        f"{solution_config.solution_name} - {solution_config.module_name}. "
        f"Version {solution_config.solution_version}"
    )


def test_user_agent_string(solution_config: SolutionConfigInputs) -> None:
    assert solution_config.get_user_agent_string() == (
        f"AWSSOLUTION/{solution_config.solution_id}/{solution_config.solution_version} AWSSOLUTION-CAPABILITY/{solution_config.capability_id}/{solution_config.solution_version}"
    )
