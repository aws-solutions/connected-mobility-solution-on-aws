# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
import aws_cdk as cdk
import pytest
from syrupy.extensions.json import JSONSnapshotExtension
from syrupy.matchers import path_type
from syrupy.types import SerializableData

# Connected Mobility Solution on AWS
from ....infrastructure.cms_provisioning_on_aws_stack import CmsProvisioningConstruct
from ....infrastructure.stacks.auxiliary_lambdas_stack import AuxiliaryLambdasStack
from ....infrastructure.stacks.common_dependencies_stack import CommonDependenciesStack
from ....infrastructure.stacks.iot_claim_provisioning_stack import (
    IoTClaimProvisioningStack,
)
from ....infrastructure.stacks.provisioning_lambdas_stack import (
    ProvisioningLambdasStack,
)


@pytest.fixture(name="snapshot_json_with_matcher")
def fixture_snapshot_json_with_matcher(snapshot: SerializableData) -> SerializableData:
    matcher = path_type(
        mapping={"^(.*)\\.S3Key$": (str,), "^(.*)\\.TemplateURL\\.(.*)$": (list,)},
        regex=True,
    )
    return snapshot.use_extension(JSONSnapshotExtension)(matcher=matcher)


@pytest.fixture(name="cms_provisioning_on_aws_stack", scope="package")
def fixture_stack() -> CmsProvisioningConstruct:
    app = cdk.Stack()
    cms_provisioning_on_aws_stack = CmsProvisioningConstruct(
        app, "cms-provisioning-on-aws-test"
    )
    return cms_provisioning_on_aws_stack


@pytest.fixture(name="iot_claim_provisioning_stack", scope="package")
def fixture_iot_provisioning_stack(
    cms_provisioning_on_aws_stack: CmsProvisioningConstruct,
) -> IoTClaimProvisioningStack:
    iot_claim_provisioning_stack = (
        cms_provisioning_on_aws_stack.iot_claim_provisioning_stack
    )
    return iot_claim_provisioning_stack


@pytest.fixture(name="provisioning_lambdas_stack", scope="package")
def fixture_provisioning_lambdas_stack(
    cms_provisioning_on_aws_stack: CmsProvisioningConstruct,
) -> ProvisioningLambdasStack:
    provisioning_lambdas_stack = (
        cms_provisioning_on_aws_stack.provisioning_lambdas_stack
    )
    return provisioning_lambdas_stack


@pytest.fixture(name="common_dependencies_stack", scope="package")
def fixture_common_dependencies_stack(
    cms_provisioning_on_aws_stack: CmsProvisioningConstruct,
) -> CommonDependenciesStack:
    common_dependencies_stack = cms_provisioning_on_aws_stack.common_dependencies_stack
    return common_dependencies_stack


@pytest.fixture(name="auxiliary_lambdas_stack", scope="package")
def fixture_auxiliary_lambdas_stack(
    cms_provisioning_on_aws_stack: CmsProvisioningConstruct,
) -> AuxiliaryLambdasStack:
    auxiliary_lambdas_stack = cms_provisioning_on_aws_stack.auxiliary_lambdas_stack
    return auxiliary_lambdas_stack
