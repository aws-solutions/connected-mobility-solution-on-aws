# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any

# Third Party Libraries
from aws_cdk import Aspects, CfnCondition, CfnMapping, Fn, Stack, Tags
from constructs import Construct
from source.infrastructure.aspects.condition_aspect import ConditionAspect

# Connected Mobility Solution on AWS
from ..constructs.app_registry import AppRegistryConstruct
from ..constructs.custom_resource_lambda import CustomResourceLambdaConstruct
from ..constructs.deployment_uuid_construct import DeploymentUUIDConstruct
from ..constructs.lambda_dependencies import LambdaDependenciesConstruct
from ..constructs.module_integration import ModuleOutputsConstruct
from ..stacks import CmsConstants
from .components.metrics import Metrics
from .components.pipelines import Pipelines
from .components.proton_environment import ProtonEnvironment


class CmsStack(Stack):
    def __init__(  # pylint: disable=too-many-locals
        self, scope: Construct, stack_id: str, **kwargs: Any
    ) -> None:
        super().__init__(scope, stack_id, **kwargs)

        solution_mapping = CfnMapping(
            self,
            "Solution",
            mapping={
                "Config": {
                    "SendAnonymousUsage": "Yes",
                }
            },
        )

        send_anonymous_usage = solution_mapping.find_in_map(
            "Config", "SendAnonymousUsage"
        )

        send_anonymous_usage_condition = CfnCondition(
            self,
            "SendAnonymousUsage",
            expression=Fn.condition_equals(send_anonymous_usage, "Yes"),
        )

        metrics_url = "https://metrics.awssolutionsbuilder.com/generic"

        dependency_layer = LambdaDependenciesConstruct(
            self,
            "cms-dependency-layer",
            dependency_layer_dir_name="cmdp_dependency_layer",
        )
        custom_resource_construct = CustomResourceLambdaConstruct(
            self,
            "cms-custom-resource",
            dependency_layer=dependency_layer.dependency_layer,
        )

        deployment_uuid_construct = DeploymentUUIDConstruct(
            self,
            "cms-deployment-uuid",
            custom_resource_lambda_arn=custom_resource_construct.custom_resource_lambda.function_arn,
        )
        deployment_uuid = (
            deployment_uuid_construct.deployment_uuid_custom_resource.get_att_string(
                "SolutionUUID"
            )
        )

        app_registry = AppRegistryConstruct(
            self,
            "cms-app-registry",
            application_name=CmsConstants.APP_NAME,
            application_type=CmsConstants.APPLICATION_TYPE,
            solution_id=CmsConstants.SOLUTION_ID,
            solution_name=CmsConstants.SOLUTION_NAME,
            solution_version=CmsConstants.SOLUTION_VERSION,
        )

        proton_environment = ProtonEnvironment(
            self,
            "cms-proton-environment",
            custom_resource_construct,
        )
        pipelines = Pipelines(
            self,
            "cms-pipelines",
        )

        metrics_construct = Metrics(
            self,
            "cms-metrics",
            metrics_url,
            deployment_uuid,
        )

        Aspects.of(metrics_construct).add(
            ConditionAspect(send_anonymous_usage_condition)
        )

        module_outputs = ModuleOutputsConstruct(
            self,
            "cms-module-outputs",
            deployment_uuid=deployment_uuid,
            resource_bucket=self.node.get_context("cms-resource-bucket"),
            resource_bucket_region=self.node.get_context("cms-resource-bucket-region"),
            resource_bucket_key_prefix=self.node.get_context(
                "cms-resource-bucket-backstage-template-key-prefix"
            ),
            resource_bucket_refresh_frequency_min=self.node.get_context(
                "cms-resource-bucket-backstage-refresh-frequency-mins"
            ),
            metrics_url=metrics_url,
            send_anonymous_usage=send_anonymous_usage,
            send_anonymous_usage_condition=send_anonymous_usage_condition,
        )

        Tags.of(app_registry).add("Solutions:DeploymentUUID", deployment_uuid)
        Tags.of(proton_environment).add("Solutions:DeploymentUUID", deployment_uuid)
        Tags.of(pipelines).add("Solutions:DeploymentUUID", deployment_uuid)
        Tags.of(module_outputs).add("Solutions:DeploymentUUID", deployment_uuid)
