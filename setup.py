# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
import setuptools

try:
    with open("README.md", "r", encoding="utf-8") as fp:
        LONG_DESCRIPTION = fp.read()
except FileNotFoundError:
    LONG_DESCRIPTION = ""


setuptools.setup(
    name="connected-mobility-solution-on-aws",
    version="1.0.2",
    description="The administrative module to deploy all CMS modules and assets",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    author="AWS WWSO Automotive Team",
    package_dir={
        "source": "./source",
        "templates": "./templates",
        "deployment": "./deployment",
    },
    packages=["source", "templates", "deployment"],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Typing :: Typed",
    ],
)
