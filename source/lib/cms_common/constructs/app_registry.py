# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from dataclasses import dataclass

# AWS Libraries
from aws_cdk import Stack, Tags, aws_servicecatalogappregistry
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
        scope: Stack,  # Scope should be the top-level stack of which we are registering
        construct_id: str,
        app_registry_inputs: AppRegistryInputs,
    ) -> None:
        super().__init__(scope, construct_id)

        region = scope.region
        account = scope.account

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

        # Add awsApplication tag to Stack resources associated with Application to "onboard" application to the myApplications dashboard
        Tags.of(scope).add(
            "awsApplication",
            cfn_application.attr_application_tag_value,
            exclude_resource_types=[cfn_application.cfn_resource_type, "aws:cdk:stack"],
        )
