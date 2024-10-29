# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os

# Third Party Libraries
from setuptools import find_packages, setup
from setuptools.command.build import build
from setuptools.command.egg_info import egg_info

# pylint: disable=attribute-defined-outside-init


class CustomDirEggInfo(egg_info):
    def initialize_options(self) -> None:
        egg_info.initialize_options(self)

        self.dist_dir = os.environ.get("MODULE_LIB_DIST_PATH", None)
        if self.dist_dir is not None:
            os.makedirs(self.dist_dir, exist_ok=True)
            self.egg_base = self.dist_dir

    def finalize_options(self) -> None:
        egg_info.finalize_options(self)
        self.announce(f"Using directory for egg_info: {self.egg_base}")


class CustomDirBuild(build):
    def initialize_options(self) -> None:
        build.initialize_options(self)

        self.dist_dir = os.environ.get("MODULE_LIB_DIST_PATH", None)
        if self.dist_dir is not None:
            os.makedirs(self.dist_dir, exist_ok=True)
            self.build_base = self.dist_dir

    def finalize_options(self) -> None:
        build.finalize_options(self)
        self.announce(f"Using directory for build: {self.build_base}")


# pylint: enable=attribute-defined-outside-init


# Explicit setup call necessary for use with `pipenv-setup`
setup(
    install_requires=[
        "aws-lambda-powertools[tracer,validation]>=2.4.0",
        "cattrs>=22.1.0",
        "toml>=0.10.2",
    ],
    name="cms_common",
    version="2.0.1",
    description="Common library used in CMS modules",
    packages=find_packages(
        exclude=[
            "*tests.*",
            "*tests",
        ],
    ),
    cmdclass={"egg_info": CustomDirEggInfo, "build": CustomDirBuild},
    package_data={"cms_common": ["py.typed"]},
    author="AWS Industrial Solutions Team",
    python_requires=">=3.12",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.12",
        "Typing :: Typed",
    ],
)
