# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import tempfile
from os.path import abspath, dirname
from typing import Any, Dict, List
from unittest.mock import MagicMock

# Third Party Libraries
import pytest
from syrupy.extensions.json import JSONSnapshotExtension
from syrupy.matchers import path_value
from syrupy.types import SerializableData

# AWS Libraries
from aws_cdk import Stack, assertions, aws_lambda

# Connected Mobility Solution on AWS
from ..app_unique_id import AppUniqueId
from ..cdk_lambda_vpc_config_construct import CDKLambdasVpcConfigConstruct
from ..cmk_encrypted_s3 import CMKEncryptedS3Construct
from ..custom_resource_lambda import CustomResourceLambdaConstruct
from ..identity_provider_config import IdentityProviderConfig
from ..lambda_dependencies import LambdaDependenciesConstruct, LambdaDependencyError
from ..vpc_construct import VpcConfig, VpcConstruct


@pytest.fixture(name="snapshot_json_with_matcher")
def fixture_snapshot_json_with_matcher(snapshot: SerializableData) -> SerializableData:
    matcher = path_value(
        mapping={
            ".*": r"(\/?([0-9a-fA-F]+)\.zip|[a-zA-Z0-9:/-]+([0-9]{12})[a-zA-Z0-9:/-]+)",
        },
        regex=True,
        types=(object,),
        replacer=lambda data, match: data.replace(match[1], "test") if match else data,
    )
    return snapshot.use_extension(JSONSnapshotExtension)(matcher=matcher)


@pytest.fixture(name="app_unique_id_stack", scope="session")
def fixture_app_unique_id_stack() -> assertions.Template:
    stack = Stack()
    AppUniqueId.create_cfn_parameter(
        stack,
    )
    return assertions.Template.from_stack(stack)


@pytest.fixture(name="identity_provider_config_stack", scope="session")
def fixture_identity_provider_config_stack() -> assertions.Template:
    stack = Stack()
    IdentityProviderConfig.create_cfn_parameter(
        stack,
    )
    return assertions.Template.from_stack(stack)


@pytest.fixture(name="app_unique_id_cfn_parameter", scope="session")
def fixture_app_unique_id_cfn_parameter(
    app_unique_id_stack: assertions.Template,
) -> Any:
    return dict(app_unique_id_stack.to_json()["Parameters"])["AppUniqueId"]


@pytest.fixture(name="cmk_encrpyted_s3_stack", scope="session")
def fixture_cmk_encrpyted_s3_stack() -> assertions.Template:
    stack = Stack()
    CMKEncryptedS3Construct(
        stack,
        "test-cmk-encrypted-s3",
    )
    return assertions.Template.from_stack(stack)


@pytest.fixture(name="empty_lambda_dependencies_stack", scope="session")
def fixture_empty_lambda_dependencies_stack() -> assertions.Template:
    with tempfile.TemporaryDirectory() as tmpdirname:
        # mock lambda code asset path
        aws_lambda.Code.from_asset = MagicMock(  # type: ignore[method-assign]
            return_value=aws_lambda.AssetCode(path=tmpdirname)
        )

        stack = Stack()
        LambdaDependenciesConstruct(
            stack,
            "test-lambda-dependencies",
            pipfile_path=f"{dirname(abspath(__file__))}/test_pipfile_empty.toml",
            dependency_layer_path=f"{dirname(abspath(__file__))}/mock_dependency_layer",
        )
        return assertions.Template.from_stack(stack)


@pytest.fixture(name="populated_lambda_dependencies_stack", scope="session")
def fixture_populated_lambda_dependencies_stack() -> assertions.Template:
    with tempfile.TemporaryDirectory() as tmpdirname:
        # mock lambda code asset path
        aws_lambda.Code.from_asset = MagicMock(  # type: ignore[method-assign]
            return_value=aws_lambda.AssetCode(path=tmpdirname)
        )

        stack = Stack()
        try:
            LambdaDependenciesConstruct(
                stack,
                "test-lambda-dependencies",
                pipfile_path=f"{dirname(abspath(__file__))}/test_pipfile_populated.toml",
                dependency_layer_path=f"{dirname(abspath(__file__))}/mock_dependency_layer",
            )
        except LambdaDependencyError:
            pass  # Error excpected because dependencies are not real
        return assertions.Template.from_stack(stack)


@pytest.fixture(name="custom_resource_lambda_stack", scope="session")
def fixture_custom_resource_lambda_stack() -> assertions.Template:
    with tempfile.TemporaryDirectory() as tmpdirname:
        # mock lambda code asset path
        aws_lambda.Code.from_asset = MagicMock(  # type: ignore[method-assign]
            return_value=aws_lambda.AssetCode(path=tmpdirname)
        )

        stack = Stack()

        vpc_construct = VpcConstruct(
            stack,
            "test-vpc-construct",
            vpc_config=VpcConfig(
                vpc_name="test-vpc-name",
                vpc_id="test-vpc-id",
                vpc_cidr_block="test-cidr-block",
                public_subnets=["test-vpc-public-subnet-1", "test-vpc-public-subnet-2"],
                private_subnets=[
                    "test-vpc-private-subnet-1",
                    "test-vpc-private-subnet-2",
                ],
                isolated_subnets=[
                    "test-vpc-isolated-subnet-1",
                    "test-vpc-isolated-subnet-2",
                ],
                availability_zones=["us-east-1", "us-east-2"],
            ),
        )

        lambda_dependencies = LambdaDependenciesConstruct(
            stack,
            "test-lambda-dependencies",
            pipfile_path=f"{dirname(abspath(__file__))}/test_pipfile_empty.toml",
            dependency_layer_path=f"{dirname(abspath(__file__))}/mock_dependency_layer",
        )
        CustomResourceLambdaConstruct(
            stack,
            "test-custom-resource-lambda",
            dependency_layer=lambda_dependencies.dependency_layer,
            asset_path="dist/lambda/custom_resource.zip",
            unique_id="test-id",
            name="test-module-name",
            user_agent_string="test-user-agent-string",
            vpc_construct=vpc_construct,
        )
        return assertions.Template.from_stack(stack)


@pytest.fixture(name="cdk_lambda_vpc_config_construct_stack_template", scope="session")
def fixture_cdk_lambda_vpc_config_construct_stack_template() -> assertions.Template:
    stack = Stack()

    vpc_construct = VpcConstruct(
        stack,
        "test-vpc-construct",
        vpc_config=VpcConfig(
            vpc_name="test-vpc-name",
            vpc_id="test-vpc-id",
            vpc_cidr_block="test-cidr-block",
            public_subnets=["test-vpc-public-subnet-1", "test-vpc-public-subnet-2"],
            private_subnets=[
                "test-vpc-private-subnet-1",
                "test-vpc-private-subnet-2",
            ],
            isolated_subnets=[
                "test-vpc-isolated-subnet-1",
                "test-vpc-isolated-subnet-2",
            ],
            availability_zones=["us-east-1", "us-east-2"],
        ),
    )

    CDKLambdasVpcConfigConstruct(
        stack,
        "test-cdk-lambda-vpc-config-construct-lambda",
        vpc_construct=vpc_construct,
        subnets=[
            "test-vpc-private-subnet-1",
            "test-vpc-private-subnet-2",
        ],
    )
    return assertions.Template.from_stack(stack)


@pytest.fixture(name="vpc_construct_stack_template", scope="session")
def fixture_vpc_construct_stack_template() -> assertions.Template:
    with tempfile.TemporaryDirectory():
        stack = Stack()
        VpcConstruct(
            stack,
            "test-vpc-construct",
            vpc_config=VpcConfig(
                vpc_name="test-vpc-name",
                vpc_id="test-vpc-id",
                vpc_cidr_block="test-cidr-block",
                public_subnets=["test-vpc-public-subnet-1", "test-vpc-public-subnet-2"],
                private_subnets=[
                    "test-vpc-private-subnet-1",
                    "test-vpc-private-subnet-2",
                ],
                isolated_subnets=[
                    "test-vpc-isolated-subnet-1",
                    "test-vpc-isolated-subnet-2",
                ],
                availability_zones=["us-east-1", "us-east-2"],
            ),
        )

        return assertions.Template.from_stack(stack)


@pytest.fixture(name="vpc_construct", scope="session")
def fixture_vpc_construct_stack() -> VpcConstruct:
    with tempfile.TemporaryDirectory():
        stack = Stack()
        vpc_construct = VpcConstruct(
            stack,
            "test-vpc-construct",
            vpc_config=VpcConfig(
                vpc_name="test-vpc-name",
                vpc_id="test-vpc-id",
                vpc_cidr_block="test-cidr-block",
                public_subnets=["test-vpc-public-subnet-1", "test-vpc-public-subnet-2"],
                private_subnets=[
                    "test-vpc-private-subnet-1",
                    "test-vpc-private-subnet-2",
                ],
                isolated_subnets=[
                    "test-vpc-isolated-subnet-1",
                    "test-vpc-isolated-subnet-2",
                ],
                availability_zones=["us-east-1", "us-east-2"],
            ),
        )

        return vpc_construct


@pytest.fixture(name="subnet_selections", scope="session")
def fixture_vpc_construct_subnet_selections() -> Dict[str, List[str]]:
    return {
        "public_subnets": ["test-vpc-public-subnet-1", "test-vpc-public-subnet-2"],
        "private_subnets": [
            "test-vpc-private-subnet-1",
            "test-vpc-private-subnet-2",
        ],
        "isolated_subnets": [
            "test-vpc-isolated-subnet-1",
            "test-vpc-isolated-subnet-2",
        ],
    }
