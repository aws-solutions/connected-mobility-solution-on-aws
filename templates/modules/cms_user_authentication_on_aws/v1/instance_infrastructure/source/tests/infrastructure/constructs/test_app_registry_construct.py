# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
from aws_cdk import Stack, assertions


def test_application(
    app_registry_stack: Stack,
) -> None:
    template = assertions.Template.from_stack(app_registry_stack)
    template.resource_count_is("AWS::ServiceCatalogAppRegistry::Application", 1)


def test_attribute_group(
    app_registry_stack: Stack,
) -> None:
    template = assertions.Template.from_stack(app_registry_stack)
    template.resource_count_is("AWS::ServiceCatalogAppRegistry::AttributeGroup", 1)


def test_attribute_group_association(
    app_registry_stack: Stack,
) -> None:
    template = assertions.Template.from_stack(app_registry_stack)
    template.resource_count_is(
        "AWS::ServiceCatalogAppRegistry::AttributeGroupAssociation", 1
    )


def test_resource_association(
    app_registry_stack: Stack,
) -> None:
    template = assertions.Template.from_stack(app_registry_stack)
    template.resource_count_is("AWS::ServiceCatalogAppRegistry::ResourceAssociation", 1)
