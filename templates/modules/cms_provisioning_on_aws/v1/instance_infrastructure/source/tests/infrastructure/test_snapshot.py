# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
import aws_cdk
from aws_cdk.assertions import Template
from syrupy.types import SerializableData

# Connected Mobility Solution on AWS
from ...infrastructure.cms_provisioning_on_aws_stack import CmsProvisioningOnAwsStack
from ...infrastructure.stacks.auxiliary_lambdas_stack import AuxiliaryLambdasStack
from ...infrastructure.stacks.common_dependencies_stack import CommonDependenciesStack
from ...infrastructure.stacks.iot_claim_provisioning_stack import (
    IoTClaimProvisioningStack,
)
from ...infrastructure.stacks.provisioning_lambdas_stack import ProvisioningLambdasStack


def test_cms_provisioning_on_aws_snapshot(
    snapshot_json_with_matcher: SerializableData,
) -> None:
    stack = aws_cdk.Stack()
    cms_provisioning_on_aws_stack = CmsProvisioningOnAwsStack(
        stack, "cms-provisioning-on-aws"
    )

    template = Template.from_stack(cms_provisioning_on_aws_stack)
    assert template.to_json() == snapshot_json_with_matcher


def test_vp_auxiliary_lambdas_snapshot(
    snapshot_json_with_matcher: SerializableData,
) -> None:
    stack = aws_cdk.Stack()
    auxiliary_lambdas_stack = AuxiliaryLambdasStack(stack, "vp-auxiliary-lambdas")

    template = Template.from_stack(auxiliary_lambdas_stack)
    assert template.to_json() == snapshot_json_with_matcher


def test_vp_common_dependencies_snapshot(
    snapshot_json_with_matcher: SerializableData,
) -> None:
    stack = aws_cdk.Stack()
    common_dependencies_stack = CommonDependenciesStack(stack, "vp-common-dependencies")

    template = Template.from_stack(common_dependencies_stack)
    assert template.to_json() == snapshot_json_with_matcher


def test_vp_iot_claim_provisioning_snapshot(
    snapshot_json_with_matcher: SerializableData,
) -> None:
    stack = aws_cdk.Stack()
    iot_claim_provisioning_stack = IoTClaimProvisioningStack(
        stack, "vp-iot-claim-provisioning"
    )

    template = Template.from_stack(iot_claim_provisioning_stack)
    assert template.to_json() == snapshot_json_with_matcher


def test_vp_provisioning_lambdas_snapshot(
    snapshot_json_with_matcher: SerializableData,
) -> None:
    stack = aws_cdk.Stack()
    provisioning_lambdas_stack = ProvisioningLambdasStack(stack, "vp-provision-lambdas")

    template = Template.from_stack(provisioning_lambdas_stack)
    assert template.to_json() == snapshot_json_with_matcher
