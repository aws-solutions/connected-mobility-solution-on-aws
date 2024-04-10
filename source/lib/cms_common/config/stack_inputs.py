# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from dataclasses import dataclass
from typing import Optional

# AWS Libraries
from aws_cdk import App, Tags


@dataclass(frozen=True)
class S3AssetConfigInputs:
    bucket_base_name: str
    object_key_prefix: str


@dataclass(frozen=True)
class SolutionConfigInputs:
    solution_name: str
    solution_id: str
    solution_version: str
    application_type: str
    module_name: str
    module_short_name: str
    capability_id: Optional[str]

    def get_user_agent_string(self) -> str:
        if self.capability_id is None:
            return f"AWSSOLUTION/{self.solution_id}/{self.solution_version}"

        return f"AWSSOLUTION/{self.solution_id}/{self.solution_version} AWSSOLUTION-CAPABILITY/{self.capability_id}/{self.solution_version}"


def create_stack_description(solution_config: SolutionConfigInputs) -> str:
    return (
        f"({solution_config.solution_id}-{solution_config.capability_id}) "
        f"{solution_config.solution_name} - {solution_config.module_name}. "
        f"Version {solution_config.solution_version}"
    )


def create_solution_tags_for_stack(
    app: App, solution_config: SolutionConfigInputs
) -> None:
    Tags.of(app).add("Solutions:ModuleName", solution_config.module_name)
    Tags.of(app).add("Solutions:SolutionName", solution_config.solution_name)
    Tags.of(app).add("Solutions:SolutionID", solution_config.solution_id)
    Tags.of(app).add("Solutions:SolutionVersion", solution_config.solution_version)
    Tags.of(app).add("Solutions:ApplicationType", solution_config.application_type)
