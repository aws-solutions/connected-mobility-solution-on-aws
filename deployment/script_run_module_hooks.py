#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import argparse
import os
import sys
from os.path import abspath, dirname, join

# Colors
MAGENTA = "\033[0;35m"
RED = "\033[91m"
NC = "\033[0m"

# File is nested twice: root/deployment/script_run_module_hooks.py
ROOT = dirname(dirname(abspath(__file__)))


def main(args: argparse.Namespace) -> None:
    module_path = args.module_path

    # Check whether venv exists for the module and log accordingly
    if not os.path.exists(f"{module_path}/.venv/bin/activate"):
        print(f"{RED}Run 'make install' before running pre-commit!\n{NC}")
        sys.exit(1)

    print(f"{MAGENTA}Activating venv found in {module_path}\n{NC}")

    # Activate virtual environment and run pre-commit using the module's config and files
    cfg = join(
        ROOT,
        module_path,
        ".pre-commit-config.yaml",
    )
    pre_commit = f"source {module_path}/.venv/bin/activate; pre-commit run --config {cfg} --files {' '.join(args.files_list)}"

    exit_status = os.system(pre_commit)  # nosec
    if os.name == "posix":
        exit_status = os.waitstatus_to_exitcode(exit_status)

    sys.exit(exit_status)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="module_pre_commit_runner",
        description="A script to run nested pre-commit configs.",
    )
    parser.add_argument(
        "--module-path",
        action="store",
        type=str,
        help="The relative path to the module.",
    )
    parser.add_argument("-f", "--files-list", nargs="+", default=[])

    main(parser.parse_args())
