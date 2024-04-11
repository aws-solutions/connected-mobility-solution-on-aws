# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
from os.path import abspath, dirname
from typing import Any

# AWS Libraries
from aws_cdk import ArnFormat, Aws, CfnMapping, Stack, aws_iam
from constructs import Construct

# CMS Common Library
from cms_common.config.resource_names import ResourceName, ResourcePrefix
from cms_common.config.stack_inputs import S3AssetConfigInputs, SolutionConfigInputs
from cms_common.constructs.app_registry import AppRegistryConstruct, AppRegistryInputs
from cms_common.constructs.app_unique_id import AppUniqueId
from cms_common.constructs.cdk_lambda_vpc_config_construct import (
    CDKLambdasVpcConfigConstruct,
)
from cms_common.constructs.custom_resource_lambda import CustomResourceLambdaConstruct
from cms_common.constructs.lambda_dependencies import LambdaDependenciesConstruct
from cms_common.constructs.vpc_construct import VpcConstruct

# Connected Mobility Solution on AWS
from .constructs.deployment_uuid import DeploymentUUIDConstruct
from .constructs.metrics import MetricsConstruct
from .constructs.module_integration import ModuleInputsConstruct, ModuleOutputsConstruct


class CmsConfigStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        solution_config_inputs: SolutionConfigInputs,
        s3_asset_config_inputs: S3AssetConfigInputs,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        solution_mapping = CfnMapping(
            self,
            "Solution",
            mapping={
                "AssetsConfig": {
                    "S3AssetBucketBaseName": s3_asset_config_inputs.bucket_base_name,
                    "S3AssetKeyPrefix": s3_asset_config_inputs.object_key_prefix,
                },
                "Config": {
                    "SendAnonymousUsage": "Yes",
                },
            },
        )

        module_inputs_construct = ModuleInputsConstruct(self, "module-inputs-construct")

        # SSM Parameter to register an app unique ID. This is done before initializing
        # any other resources so that the stack creation fails early if another stack
        # with the same app unique ID is already deployed.
        app_unique_id_ssm_parameter = AppUniqueId.register(
            self, app_unique_id=module_inputs_construct.app_unique_id
        )

        self.cms_config_construct = CmsConfigConstruct(
            self,
            "cms-config",
            solution_mapping=solution_mapping,
            solution_config_inputs=solution_config_inputs,
            module_inputs_construct=module_inputs_construct,
        )
        self.cms_config_construct.node.add_dependency(app_unique_id_ssm_parameter)


class CmsConfigConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        solution_mapping: CfnMapping,
        solution_config_inputs: SolutionConfigInputs,
        module_inputs_construct: ModuleInputsConstruct,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        metrics_url = "https://metrics.awssolutionsbuilder.com/generic"

        AppRegistryConstruct(
            self,
            "app-registry-construct",
            app_registry_inputs=AppRegistryInputs(
                application_name=Aws.STACK_NAME,
                application_type=solution_config_inputs.application_type,
                solution_id=solution_config_inputs.solution_id,
                solution_name=solution_config_inputs.solution_name,
                solution_version=solution_config_inputs.solution_version,
            ),
        )

        vpc_construct = VpcConstruct(
            self, "vpc-construct", vpc_config=module_inputs_construct.vpc_config
        )

        self.cdk_lambdas_vpc_construct = CDKLambdasVpcConfigConstruct(
            self,
            "cdk-lambdas-vpc-construct",
            vpc_construct=vpc_construct,
            subnets=module_inputs_construct.vpc_config.private_subnets,
        )

        lambda_dependencies_construct = LambdaDependenciesConstruct(
            self,
            "dependency-layer-construct",
            pipfile_path=f"{dirname(dirname(dirname(abspath(__file__))))}/Pipfile",
            dependency_layer_path=f"{os.getcwd()}/source/infrastructure/cms_config_dependency_layer",
        )

        custom_resource_lambda_construct = CustomResourceLambdaConstruct(
            self,
            "custom-resource-lambda-construct",
            dependency_layer=lambda_dependencies_construct.dependency_layer,
            unique_id=module_inputs_construct.app_unique_id,
            name=solution_config_inputs.module_short_name,
            asset_path="dist/lambda/custom_resource.zip",
            user_agent_string=solution_config_inputs.get_user_agent_string(),
            vpc_construct=vpc_construct,
        )

        deployment_uuid_construct = DeploymentUUIDConstruct(
            self,
            "deployment-uuid-construct",
            custom_resource_lambda_function_arn=custom_resource_lambda_construct.function.function_arn,
        )

        metrics_construct = MetricsConstruct(
            self,
            "metrics-construct",
            metrics_url=metrics_url,
            deployment_uuid=deployment_uuid_construct.uuid,
            dependency_layer=lambda_dependencies_construct.dependency_layer,
            solution_mapping=solution_mapping,
            solution_config_inputs=solution_config_inputs,
            metrics_lambda_function_name=ResourceName.hyphen_separated(
                prefix=ResourcePrefix.hyphen_separated(
                    app_unique_id=module_inputs_construct.app_unique_id,
                    module_name=solution_config_inputs.module_short_name,
                ),
                name="anonymous-metrics",
            ),
            vpc_construct=vpc_construct,
        )

        aws_resource_lookup_lambda_construct = CustomResourceLambdaConstruct(
            self,
            "aws-resource-lookup-custom-resource-lambda",
            dependency_layer=lambda_dependencies_construct.dependency_layer,
            unique_id=module_inputs_construct.app_unique_id,
            name=solution_config_inputs.module_short_name,
            asset_path="dist/lambda/aws_resource_lookup.zip",
            suffix="aws-resource-lookup",
            user_agent_string=solution_config_inputs.get_user_agent_string(),
            vpc_construct=vpc_construct,
        )

        module_outputs_construct = ModuleOutputsConstruct(
            self,
            "module-outputs-construct",
            deployment_uuid=deployment_uuid_construct.uuid,
            module_inputs_construct=module_inputs_construct,
            metrics_url=metrics_url,
            metrics_construct=metrics_construct,
            vpc_config=module_inputs_construct.vpc_config,
            vpc_name_provider_construct=aws_resource_lookup_lambda_construct,
        )

        aws_resource_lookup_lambda_construct.add_policy_to_custom_resource_lambda(
            aws_iam.Policy(
                self,
                "ssm",
                document=aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=["ssm:GetParameter"],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="ssm",
                                    resource="parameter",
                                    resource_name=f"{module_outputs_construct.ssm_prefix_without_leading_slash}/*",  # Allow read of any SSM parameter from cms_config
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                            ],
                        ),
                    ]
                ),
            )
        )
