# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from dataclasses import dataclass

# AWS Libraries
from aws_cdk import Stack, aws_servicecatalogappregistry
from constructs import Construct


@dataclass(frozen=True)
class AppRegistryInputs:
    application_name: str
    application_type: str
    solution_id: str
    solution_name: str
    solution_version: str


class AppRegistryConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_registry_inputs: AppRegistryInputs,
    ) -> None:
        super().__init__(scope, construct_id)

        region = Stack.of(self).region
        account = Stack.of(self).account

        cfn_application = aws_servicecatalogappregistry.CfnApplication(
            self,
            "app-registry-application",
            name=f"{app_registry_inputs.application_name}-{region}-{account}",
        )

        attribute_group = aws_servicecatalogappregistry.CfnAttributeGroup(
            self,
            "default-application-attributes",
            name=f"{app_registry_inputs.application_name}-{region}-{account}",
            description="Attribute group for solution information",
            attributes={
                "ApplicationType": app_registry_inputs.application_type,
                "Version": app_registry_inputs.solution_version,
                "SolutionID": app_registry_inputs.solution_id,
                "SolutionName": app_registry_inputs.solution_name,
            },
        )

        # Associate attribute group with registry
        aws_servicecatalogappregistry.CfnAttributeGroupAssociation(
            self,
            "app-registry-application-attribute-association",
            application=cfn_application.attr_id,
            attribute_group=attribute_group.attr_id,
        )

        # Associate stacks with application registry, including this stack.
        for child in Stack.of(self).node.find_all():
            if Stack.is_stack(child):
                stack = Stack.of(child)
                aws_servicecatalogappregistry.CfnResourceAssociation(
                    stack,
                    "app-registry-application-stack-association",
                    application=cfn_application.attr_id,
                    resource=stack.stack_id,
                    resource_type="CFN_STACK",
                )
