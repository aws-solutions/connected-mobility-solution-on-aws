# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
import aws_cdk as cdk
import pytest
from aws_cdk import App, Stack, aws_kms
from constructs import Construct
from syrupy.extensions.json import JSONSnapshotExtension
from syrupy.matchers import path_type
from syrupy.types import SerializableData

# Connected Mobility Solution on AWS
from ....infrastructure.cms_vehicle_simulator_on_aws_stack import (
    CmsVehicleSimulatorConstruct,
    InfrastructureCloudFrontStack,
    InfrastructureCognitoStack,
    InfrastructureConsoleStack,
    InfrastructureGeneralStack,
    InfrastructureResourceStack,
    InfrastructureSimulatorStack,
    VSApiStack,
)


class NagTestStack(Stack):
    def __init__(self, scope: Construct, construct_id: str) -> None:
        super().__init__(scope, construct_id)
        self.test_key = aws_kms.Key(
            self,
            "nag-test-key",
            enable_key_rotation=True,
        )


@pytest.fixture(name="snapshot_json_with_matcher")
def fixture_snapshot_json_with_matcher(snapshot: SerializableData) -> SerializableData:
    matcher = path_type(
        mapping={
            "^(.*)\\.S3Key$": (str,),
            "^(.*)\\.TemplateURL\\.(.*)$": (list,),
            "^(.*)\\.SourceObjectKeys\\.(.*)$": (
                list,
                str,
            ),
        },
        regex=True,
    )
    return snapshot.use_extension(JSONSnapshotExtension)(matcher=matcher)


@pytest.fixture(name="cms_vehicle_simulator_on_aws_stack", scope="package")
def fixture_stack() -> CmsVehicleSimulatorConstruct:
    app = cdk.Stack()
    vehicle_simulator_stack = CmsVehicleSimulatorConstruct(
        app, "cms-vehicle-simulator-test"
    )
    return vehicle_simulator_stack


@pytest.fixture(name="general_stack", scope="package")
def fixture_general_stack(
    cms_vehicle_simulator_on_aws_stack: CmsVehicleSimulatorConstruct,
) -> InfrastructureGeneralStack:
    general_stack = cms_vehicle_simulator_on_aws_stack.general_stack
    return general_stack


@pytest.fixture(name="custom_resource_stack", scope="package")
def fixture_resource_stack(
    cms_vehicle_simulator_on_aws_stack: CmsVehicleSimulatorConstruct,
) -> InfrastructureResourceStack:
    resource_stack = cms_vehicle_simulator_on_aws_stack.resource_stack
    return resource_stack


@pytest.fixture(name="cognito_stack", scope="package")
def fixture_cognito_stack(
    cms_vehicle_simulator_on_aws_stack: CmsVehicleSimulatorConstruct,
) -> InfrastructureCognitoStack:
    cognito_stack = cms_vehicle_simulator_on_aws_stack.cognito_stack
    return cognito_stack


@pytest.fixture(name="cloudfront_stack", scope="package")
def fixture_cloudfront_stack(
    cms_vehicle_simulator_on_aws_stack: CmsVehicleSimulatorConstruct,
) -> InfrastructureCloudFrontStack:
    cloudfront_stack = cms_vehicle_simulator_on_aws_stack.cloudfront_stack
    return cloudfront_stack


@pytest.fixture(name="console_stack", scope="package")
def fixture_console_stack(
    cms_vehicle_simulator_on_aws_stack: CmsVehicleSimulatorConstruct,
) -> InfrastructureConsoleStack:
    console_stack = cms_vehicle_simulator_on_aws_stack.console_stack
    return console_stack


@pytest.fixture(name="simulator_stack", scope="package")
def fixture_simulator_stack(
    cms_vehicle_simulator_on_aws_stack: CmsVehicleSimulatorConstruct,
) -> InfrastructureSimulatorStack:
    simulator_stack = cms_vehicle_simulator_on_aws_stack.simulator_stack
    return simulator_stack


@pytest.fixture(name="vsapi_stack", scope="package")
def fixture_vsapi_stack(
    cms_vehicle_simulator_on_aws_stack: CmsVehicleSimulatorConstruct,
) -> VSApiStack:
    vsapi_stack = cms_vehicle_simulator_on_aws_stack.vsapi_stack
    return vsapi_stack


@pytest.fixture(name="test_stack", scope="package")
def fixture_test_stack() -> NagTestStack:
    app = App()
    test_stack = NagTestStack(app, "nag-test-stack")
    return test_stack
