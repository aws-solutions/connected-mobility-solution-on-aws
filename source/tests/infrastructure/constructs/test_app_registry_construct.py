# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library

# Third Party Libraries
import aws_cdk
from aws_cdk.assertions import Template

# Connected Mobility Solution on AWS
from ....infrastructure.stacks.cms_stack import CmsStack

app = aws_cdk.App(
    context={
        "backstage-name": "Name not set",
        "backstage-org": "Org not set",
        "user-email": "me@domain.tld",
        "route53-zone-name": "domain.tld",
        "route53-base-domain": "subdomain.domain.tld",
        "web-port": "443",
        "web-scheme": "https",
        "vpc-cidr-range": "10.0.0.0/16",
        "backstage-log-level": "debug",
        "cms-resource-bucket": "my-cms-bucket",
        "cms-resource-bucket-region": "us-east-1",
        "cms-resource-bucket-backstage-template-key-prefix": "v0.0.0/backstage/templates",
        "cms-resource-bucket-backstage-refresh-frequency-mins": "30",
    }
)
stack = CmsStack(app, "cms-on-aws")
template = Template.from_stack(stack)


def test_application() -> None:
    template.resource_count_is("AWS::ServiceCatalogAppRegistry::Application", 1)


def test_attribute_group() -> None:
    template.resource_count_is("AWS::ServiceCatalogAppRegistry::AttributeGroup", 1)


def test_attribute_group_association() -> None:
    template.resource_count_is(
        "AWS::ServiceCatalogAppRegistry::AttributeGroupAssociation", 1
    )


def test_resource_association() -> None:
    template.resource_count_is("AWS::ServiceCatalogAppRegistry::ResourceAssociation", 1)
