# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
from typing import Any, List

# AWS Libraries
from aws_cdk import Aws, CfnMapping, Duration, Stack, Tags, aws_rds, aws_ssm
from constructs import Construct

# CMS Common Library
from cms_common.config.resource_names import ResourceName
from cms_common.config.stack_inputs import S3AssetConfigInputs, SolutionConfigInputs
from cms_common.constructs.app_registry import AppRegistryConstruct, AppRegistryInputs
from cms_common.constructs.app_unique_id import AppUniqueId
from cms_common.constructs.cdk_lambda_vpc_config_construct import (
    CDKLambdasVpcConfigConstruct,
)
from cms_common.constructs.vpc_construct import VpcConstruct

# Connected Mobility Solution on AWS
from .constructs.aurora_database import AuroraDatabaseConstruct
from .constructs.backstage_container import BackstageContainerConstruct
from .constructs.cognito_user import CognitoUserConstruct
from .constructs.load_balancer import LoadBalancerConstruct
from .constructs.module_integration import ModuleInputsConstruct
from .constructs.multi_account_construct import MultiAccountConstruct


class AcdpBackstageStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        solution_config_inputs: SolutionConfigInputs,
        s3_asset_config_inputs: S3AssetConfigInputs,
        s3_asset_bucket_name: str,
        *args: List[Any],
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, *args, **kwargs)

        solution_mapping = CfnMapping(
            self,
            "Solution",
            mapping={
                "AssetsConfig": {
                    "S3AssetBucketName": s3_asset_bucket_name,
                    "S3AssetKeyPrefix": s3_asset_config_inputs.object_key_prefix,
                },
                "Config": {
                    "SendAnonymousUsage": "Yes",
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

        module_inputs = ModuleInputsConstruct(
            self,
            "module-inputs-construct",
            solution_config_inputs=solution_config_inputs,
            solution_mapping=solution_mapping,
        )

        # Check if a config stack for the app unique id is registered. Fail stack
        # creation if it is not registered. If config stack exists, then create an SSM
        # parameter to register the module with the app unique id.
        register_module_with_app_unique_id = AppUniqueId.register_module(
            self,
            app_unique_id=module_inputs.acdp_uid,
            module_name=solution_config_inputs.module_short_name,
        )

        deployment_uuid = aws_ssm.StringParameter.from_string_parameter_attributes(
            self,
            "deployment-uuid",
            parameter_name=ResourceName.slash_separated(
                prefix=module_inputs.acdp_config_ssm_prefix_with_slash_prefix,
                name="deployment-uuid",
            ),
            simple_name=False,
            force_dynamic_reference=True,
        ).string_value

        self.backstage_construct = AcdpBackstageConstruct(
            self, "acdp-backstage", module_inputs=module_inputs
        )
        self.backstage_construct.node.add_dependency(register_module_with_app_unique_id)

        Tags.of(self.backstage_construct).add(
            "Solutions:DeploymentUUID", deployment_uuid
        )


class AcdpBackstageConstruct(Construct):
    def __init__(  # pylint: disable=too-many-locals
        self,
        scope: Construct,
        construct_id: str,
        module_inputs: ModuleInputsConstruct,
    ) -> None:
        super().__init__(scope, construct_id)

        vpc_construct = VpcConstruct(
            self, "vpc-construct", vpc_config=module_inputs.vpc_config
        )

        self.cdk_lambdas_vpc_construct = CDKLambdasVpcConfigConstruct(
            self,
            "cdk-lambdas-vpc-construct",
            vpc_construct=vpc_construct,
            subnets=module_inputs.vpc_config.private_subnets,
        )

        CognitoUserConstruct(
            self,
            "cognito-user-construct",
            module_inputs=module_inputs,
        )

        aurora_database_construct = AuroraDatabaseConstruct(
            self,
            "aurora-database-construct",
            vpc=vpc_construct.vpc,
            isolated_subnets=vpc_construct.isolated_subnet_selection,
            credentials_secret_name=f"{module_inputs.acdp_config_ssm_prefix_with_slash_prefix}/backstage/db_credentials",
            cluster_engine=aws_rds.DatabaseClusterEngine.aurora_postgres(
                version=aws_rds.AuroraPostgresEngineVersion.VER_13_16
            ),
            rotation_interval_days=Duration.days(90),
        )

        backstage_container_construct = BackstageContainerConstruct(
            self,
            "backstage-container-construct",
            module_inputs=module_inputs,
            postgres_database_construct=aurora_database_construct,
            vpc=vpc_construct.vpc,
            private_subnets=vpc_construct.private_subnet_selection,
        )

        MultiAccountConstruct(
            self,
            "multi-account-construct",
            module_inputs=module_inputs,
            backstage_container_construct=backstage_container_construct,
        )

        LoadBalancerConstruct(
            self,
            "load-balancer-construct",
            module_inputs=module_inputs,
            backstage_container_construct=backstage_container_construct,
            vpc=vpc_construct.vpc,
            public_subnets=vpc_construct.public_subnet_selection,
            # Workaround for tokens not supported by ALB
            is_internet_facing=os.environ.get("IS_PUBLIC_FACING", "true") == "true",
        )
