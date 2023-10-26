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
from aws_cdk import NestedStack, aws_lambda, aws_ssm
from constructs import Construct

# Connected Mobility Solution on AWS
from ...config.constants import VPConstants


class CommonDependenciesStack(NestedStack):
    def __init__(self, scope: Construct, stack_id: str, **kwargs: Any) -> None:
        super().__init__(scope, stack_id, **kwargs)

        # Setup our dependency layer, and return it to provide to our lambda function. This excludes boto3 and aws-cdk-lib.
        self.dependency_layer = self.package_dependency_layer(
            dir_path=f"{os.getcwd()}/source/infrastructure/provisioning_dependency_layer",
        )

        aws_ssm.StringParameter(
            self,
            "vehicle-provisioning-dependency-layer-arn-value",
            string_value=self.dependency_layer.layer_version_arn,
            description="Arn for vehicle provisioning dependency layer",
            parameter_name=f"/{VPConstants.STAGE}/{VPConstants.APP_NAME}/arns/dependency-layer-arn",
        )

    def package_dependency_layer(
        self,
        dir_path: str = dirname(abspath(__file__)),
    ) -> aws_lambda.LayerVersion:
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

        dependency_layer = aws_lambda.LayerVersion(
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

        return dependency_layer

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
