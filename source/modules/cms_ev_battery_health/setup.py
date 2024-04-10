# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os

# Third Party Libraries
import setuptools

try:
    with open("README.md", "r", encoding="utf-8") as fp:
        LONG_DESCRIPTION = fp.read()
except FileNotFoundError:
    LONG_DESCRIPTION = ""

setuptools.setup(
    name=os.environ["MODULE_NAME"],
    version=setuptools.sic(os.environ["MODULE_VERSION"]),
    description=os.environ["MODULE_DESCRIPTION"],
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    author=os.environ["MODULE_AUTHOR"],
    python_requires=f">={os.environ['PYTHON_MINIMUM_VERSION_SUPPORTED']}",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: JavaScript",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Typing :: Typed",
    ],
)
