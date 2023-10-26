# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
import pathlib
from io import TextIOWrapper
from os.path import abspath, dirname
from typing import Any

# Third Party Libraries
import toml
from aws_cdk import aws_lambda
from constructs import Construct


class LambdaDependenciesConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        dependency_layer_dir_name: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        dir_path = f"{os.getcwd()}/source/infrastructure/{dependency_layer_dir_name}"
        project_dir = f"{dirname(dirname(dirname(dirname(abspath(__file__)))))}"
        source_pipfile = f"{project_dir}/Pipfile"
        pip_path = f"{dir_path}/python"

        # Create the folders out to the build directory
        pathlib.Path(pip_path).mkdir(parents=True, exist_ok=True)
        requirements = f"{dir_path}/requirements.txt"

        # Copy Pipfile to build directory as requirements.txt format and excluding the large packages
        with open(source_pipfile, "r", encoding="utf-8") as pipfile:
            new_pipfile = toml.load(pipfile)
        with open(requirements, "w", encoding="utf-8") as requirements_file:

            for package, constraint in new_pipfile["packages"].items():
                if package not in ["boto3", "aws-cdk-lib"]:
                    self.req_formatter(
                        package=package,
                        constraint=constraint,
                        requirements_file=requirements_file,
                    )

        # Install the requirements in the build directory (CDK will use this whole folder to build the zip)
        os.system(  # nosec
            f"/bin/bash -c 'python -m pip install -q --upgrade --target {pip_path} --requirement {requirements}'"
            # f" && find {dir_path} -name \\*.so -exec strip \\{{\\}} \\;'"
        )

        self.dependency_layer = aws_lambda.LayerVersion(
            self,
            "lambda-dependency-layer-version",
            code=aws_lambda.Code.from_asset(dir_path),
            compatible_architectures=[
                aws_lambda.Architecture.X86_64,
                aws_lambda.Architecture.ARM_64,
            ],
            compatible_runtimes=[
                aws_lambda.Runtime.PYTHON_3_8,
                aws_lambda.Runtime.PYTHON_3_9,
                aws_lambda.Runtime.PYTHON_3_10,
            ],
        )

    def req_formatter(
        self, package: str, constraint: Any, requirements_file: TextIOWrapper
    ) -> None:
        if constraint == "*":
            requirements_file.write(package + "\n")
        else:
            try:
                extras = (
                    str(constraint.get("extras", "all"))
                    .replace("'", "")
                    .replace('"', "")
                )

                # Requirements.txt wildcards are done by not specifying a version, replace with empty string instead
                version = constraint["version"] if constraint["version"] != "*" else ""

                requirements_file.write(f"{package}{extras} {version}\n")
            except (TypeError, KeyError, AttributeError):
                if isinstance(constraint, str):
                    requirements_file.write(f"{package} {constraint}\n")
