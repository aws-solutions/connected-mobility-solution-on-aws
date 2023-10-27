# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
import aws_cdk
from aws_cdk.assertions import Template
from syrupy.types import SerializableData

# Connected Mobility Solution on AWS
from ...infrastructure.cms_connect_store_on_aws_stack import CmsConnectStoreOnAwsStack


def test_connect_and_store_snapshot(
    snapshot_json_with_matcher: SerializableData,
) -> None:
    stack = aws_cdk.Stack()
    connect_and_store_stack = CmsConnectStoreOnAwsStack(
        stack, "Cms-connect-store-on-aws-stack"
    )

    template = Template.from_stack(connect_and_store_stack)
    assert template.to_json() == snapshot_json_with_matcher
