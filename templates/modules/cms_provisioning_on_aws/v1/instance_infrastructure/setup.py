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
    name="cms-provisioning-on-aws",
    version="0.0.1",
    description="A CDK Python app to provision vehicles",
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    author="AWS WWSO Automotive Team",
    install_requires=[
        "aws-cdk-lib==2.49.0",
        "constructs>=10.0.0",
        "aws_lambda_powertools",
        "types-boto3",
        "types-setuptools",
    ],
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
