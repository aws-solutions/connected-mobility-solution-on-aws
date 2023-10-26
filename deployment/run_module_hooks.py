#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import argparse
import os
import sys
from os.path import dirname, join, realpath

ROOT = dirname(dirname(realpath(__file__)))


def main(args: argparse.Namespace) -> None:
    module_path = (
        f"templates/modules/cms_{args.module}_on_aws/v1/instance_infrastructure"
    )

    # Check whether venv exists for the module and log accordingly
    separator = "===================================================="
    if not os.path.exists(f"{module_path}/.venv/bin/activate"):
        print(
            f"{separator}\n Run 'make install' before running pre-commit! \n{separator}\n"
        )
        sys.exit(1)

    print(f"{separator}\n Activating venv found in {module_path} \n{separator}\n")

    # Activate virtual environment and run precommit using the module's config and files
    cfg = join(
        ROOT,
        module_path,
        ".pre-commit-config.yaml",
    )
    precommit = f"source {module_path}/.venv/bin/activate; pre-commit run --config {cfg} --files {' '.join(args.files_list)}"

    exit_status = os.system(precommit)  # nosec
    if os.name == "posix":
        exit_status = os.waitstatus_to_exitcode(exit_status)

    sys.exit(exit_status)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="module_pre_commit_runner",
        description="A script to run nested pre-commit configs.",
    )
    parser.add_argument(
        "--module",
        action="store",
        type=str,
        default="alerts",
        help="The name of the module.",
    )
    parser.add_argument("-f", "--files-list", nargs="+", default=[])

    main(parser.parse_args())
