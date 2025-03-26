# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import pathlib
import shutil
import subprocess  # nosec
from typing import Any

# AWS Libraries
from aws_cdk import aws_lambda
from constructs import Construct


class LambdaDependencyError(Exception):
    def __init__(
        self,
        message: str = "Failed to install lambda dependencies while building lambda layer.",
        code: int = 500,
    ):
        self.message = message
        self.code = code


class LambdaDependenciesConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        pipfile_lock_dir: str,
        dependency_layer_path: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Define and create the installation directory
        installation_path = f"{dependency_layer_path}/python"
        shutil.rmtree(installation_path, ignore_errors=True)
        pathlib.Path(installation_path).mkdir(parents=True, exist_ok=True)

        # Define the requirements.txt path, and create the file from Pipfile.lock using `pipenv requirements`
        requirements_path = f"{dependency_layer_path}/requirements.txt"
        try:
            with open(requirements_path, "w", encoding="utf-8") as requirements_file:
                subprocess.run(  # nosec
                    [
                        "pipenv",
                        "requirements",
                        "--categories",
                        "packages",
                        "--exclude-markers",
                    ],
                    stdout=requirements_file,
                    check=True,
                    cwd=pipfile_lock_dir,
                )

                # Remove the "editable" flag (-e) to allow for proper installation of editables libs (e.g. cms_common) into the dependency layer
                with open(requirements_path, "r", encoding="utf-8") as file:
                    lines = file.readlines()

                modified_lines = [
                    line.replace("-e ", "", 1) if line.startswith("-e ") else line
                    for line in lines
                ]

                with open(requirements_path, "w", encoding="utf-8") as file:
                    file.writelines(modified_lines)
        except Exception as e:  # pylint: disable=broad-exception-caught
            raise LambdaDependencyError(
                "Failed to generate requirements.txt file for Lambda dependency layer."
            ) from e

        try:
            subprocess.run(  # nosec
                [
                    "python",
                    "-m",
                    "pip",
                    "install",
                    "-q",
                    "--platform",
                    "manylinux2014_x86_64",
                    "--python-version",
                    "3.12",
                    "--implementation",
                    "cp",
                    "--only-binary=:all:",
                    "--no-cache-dir",
                    "--target",
                    installation_path,
                    "--requirement",
                    requirements_path,
                ],
                check=True,
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            raise LambdaDependencyError(
                "Failed to install from requirements.txt file for Lambda dependency layer."
            ) from e

        # Create the dependency layer using the dependency_layer_path directory
        self.dependency_layer = aws_lambda.LayerVersion(
            self,
            "lambda-dependency-layer-version",
            code=aws_lambda.Code.from_asset(
                dependency_layer_path,
                exclude=["**/tests/*"],
            ),
            compatible_architectures=[
                aws_lambda.Architecture.X86_64,
                aws_lambda.Architecture.ARM_64,
            ],
            compatible_runtimes=[
                aws_lambda.Runtime.PYTHON_3_12,
            ],
        )
