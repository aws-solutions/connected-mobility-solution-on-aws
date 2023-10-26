# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library

# Third Party Libraries
from aws_cdk import assertions

# Connected Mobility Solution on AWS
from ....infrastructure.stacks.iot_claim_provisioning_stack import (
    IoTClaimProvisioningStack,
)


def test_role_count(
    iot_claim_provisioning_stack: IoTClaimProvisioningStack,
) -> None:
    template = assertions.Template.from_stack(iot_claim_provisioning_stack)
    template.resource_count_is("AWS::IAM::Role", 1)


def test_iot_policy_count(
    iot_claim_provisioning_stack: IoTClaimProvisioningStack,
) -> None:
    template = assertions.Template.from_stack(iot_claim_provisioning_stack)
    template.resource_count_is("AWS::IoT::Policy", 1)


def test_provisioning_template_count(
    iot_claim_provisioning_stack: IoTClaimProvisioningStack,
) -> None:
    template = assertions.Template.from_stack(iot_claim_provisioning_stack)
    template.resource_count_is("AWS::IoT::ProvisioningTemplate", 1)


def test_certificate_count(
    iot_claim_provisioning_stack: IoTClaimProvisioningStack,
) -> None:
    template = assertions.Template.from_stack(iot_claim_provisioning_stack)
    template.resource_count_is("AWS::IoT::Certificate", 1)


def test_policy_principal_attachment_count(
    iot_claim_provisioning_stack: IoTClaimProvisioningStack,
) -> None:
    template = assertions.Template.from_stack(iot_claim_provisioning_stack)
    template.resource_count_is("AWS::IoT::PolicyPrincipalAttachment", 1)


def test_update_event_configurations_custom_resource_count(
    iot_claim_provisioning_stack: IoTClaimProvisioningStack,
) -> None:
    template = assertions.Template.from_stack(iot_claim_provisioning_stack)
    template.resource_count_is("Custom::UpdateEventConfigurations", 1)


def test_load_or_create_iot_credentials_custom_resource_count(
    iot_claim_provisioning_stack: IoTClaimProvisioningStack,
) -> None:
    template = assertions.Template.from_stack(iot_claim_provisioning_stack)
    template.resource_count_is("Custom::LoadOrCreateIoTCredentials", 1)
