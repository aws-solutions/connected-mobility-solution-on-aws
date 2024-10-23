# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
from os.path import abspath, dirname
from typing import Any

# AWS Libraries
from aws_cdk import Aws, CfnMapping, Stack, Tags
from constructs import Construct

# CMS Common Library
from cms_common.config.resource_names import ResourceName, ResourcePrefix
from cms_common.config.ssm import get_resolvable_ssm_deployment_uuid
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
from .constructs.initial_connection import InitialConnectionConstruct
from .constructs.iot_credentials import IoTCredentialsConstruct
from .constructs.iot_provisioning_certificate import IoTProvisioningCertificateConstruct
from .constructs.iot_provisioning_template import IoTProvisioningTemplateConstruct
from .constructs.module_integration import ModuleInputsConstruct
from .constructs.post_provisioning import PostProvisioningConstruct
from .constructs.pre_provisioning import PreProvisioningConstruct
from .constructs.provisioning_database import ProvisioningDatabaseConstruct


class CmsProvisioningStack(Stack):
    def __init__(
        self,
        scope: Construct,
        stack_id: str,
        solution_config_inputs: SolutionConfigInputs,
        s3_asset_config_inputs: S3AssetConfigInputs,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, stack_id, **kwargs)

        CfnMapping(
            self,
            "Solution",
            mapping={
                "AssetsConfig": {
                    "S3AssetBucketBaseName": s3_asset_config_inputs.bucket_base_name,
                    "S3AssetKeyPrefix": s3_asset_config_inputs.object_key_prefix,
                },
            },
        )

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

        module_inputs_construct = ModuleInputsConstruct(self, "module-inputs-construct")
        app_unique_id = module_inputs_construct.app_unique_id

        # Check if a config stack for the app unique id is registered. Fail stack
        # creation if it is not registered. If config stack exists, then create an SSM
        # parameter to register the module with the app unique id.
        register_module_with_app_unique_id = AppUniqueId.register_module(
            self,
            app_unique_id=app_unique_id,
            module_name=solution_config_inputs.module_short_name,
        )

        deployment_uuid = get_resolvable_ssm_deployment_uuid(
            app_unique_id=app_unique_id
        )

        self.provisioning_construct = CmsProvisioningConstruct(
            self,
            "cms-provisioning",
            app_unique_id=app_unique_id,
            solution_config_inputs=solution_config_inputs,
            module_inputs_construct=module_inputs_construct,
        )
        self.provisioning_construct.node.add_dependency(
            register_module_with_app_unique_id
        )

        Tags.of(self.provisioning_construct).add(
            "Solutions:DeploymentUUID", deployment_uuid
        )


class CmsProvisioningConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        stack_id: str,
        app_unique_id: str,
        solution_config_inputs: SolutionConfigInputs,
        module_inputs_construct: ModuleInputsConstruct,
    ) -> None:
        super().__init__(scope, stack_id)

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
            dependency_layer_path=f"{os.getcwd()}/source/infrastructure/cms_provisioning_dependency_layer",
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

        provisioning_database_constuct = ProvisioningDatabaseConstruct(
            self, "provisioning-database-construct"
        )

        pre_provisioning_construct = PreProvisioningConstruct(
            self,
            "pre-provisioning-construct",
            dependency_layer=lambda_dependencies_construct.dependency_layer,
            provisioning_db_resources=provisioning_database_constuct.db_resources,
            app_unique_id=app_unique_id,
            solution_config_inputs=solution_config_inputs,
            vpc_construct=vpc_construct,
        )

        claim_cert_provisioning_policy_name = ResourceName.hyphen_separated(
            prefix=ResourcePrefix.hyphen_separated(
                app_unique_id=app_unique_id,
                module_name=solution_config_inputs.module_short_name,
            ),
            name="claim-cert-provisioning-policy",
        )
        iot_credentials_construct = IoTCredentialsConstruct(
            self,
            "iot-credentials-construct",
            app_unique_id=app_unique_id,
            solution_config_inputs=solution_config_inputs,
            dependency_layer=lambda_dependencies_construct.dependency_layer,
            custom_resource_lambda_construct=custom_resource_lambda_construct,
            claim_cert_provisioning_policy_name=claim_cert_provisioning_policy_name,
            vpc_construct=vpc_construct,
        )

        provisioning_template_name = ResourceName.hyphen_separated(
            prefix=ResourcePrefix.hyphen_separated(
                app_unique_id=app_unique_id,
                module_name="",  # omitting module name because the CfnProvisioningTemplate name can contain a maximum of 36 characters
            ),
            name="provisioning-template",
        )
        iot_provisioning_template_construct = IoTProvisioningTemplateConstruct(
            self,
            "iot-provisioning-template-construct",
            provisioning_template_txt=self.read_provisioning_template(),
            pre_provisioning_lambda_arn=pre_provisioning_construct.pre_provisioning_lambda_function.function_arn,
            provisioning_template_name=provisioning_template_name,
        )
        iot_provisioning_template_construct.node.add_dependency(
            pre_provisioning_construct
        )

        IoTProvisioningCertificateConstruct(
            self,
            "iot-provisioning-certificate-construct",
            custom_resource_lambda_construct=custom_resource_lambda_construct,
            iot_credentials=iot_credentials_construct.credentials.get_att(
                "CERTIFICATE_PEM"
            ).to_string(),
            provisioning_template_name=provisioning_template_name,
            claim_cert_provisioning_policy_name=claim_cert_provisioning_policy_name,
        )

        PostProvisioningConstruct(
            self,
            "post-provisioning-construct",
            dependency_layer=lambda_dependencies_construct.dependency_layer,
            custom_resource_lambda_construct=custom_resource_lambda_construct,
            provisioning_db_resources=provisioning_database_constuct.db_resources,
            app_unique_id=app_unique_id,
            solution_config_inputs=solution_config_inputs,
            provisioning_template_name=provisioning_template_name,
            vpc_construct=vpc_construct,
        )

        InitialConnectionConstruct(
            self,
            "initial-connection-construct",
            dependency_layer=lambda_dependencies_construct.dependency_layer,
            provisioning_db_resources=provisioning_database_constuct.db_resources,
            app_unique_id=app_unique_id,
            solution_config_inputs=solution_config_inputs,
            vpc_construct=vpc_construct,
        )

    def read_provisioning_template(self) -> str:
        with open("provisioning_template.json", encoding="utf-8") as file:
            template_text = file.read()
        return template_text
