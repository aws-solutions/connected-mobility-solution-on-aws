# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
from typing import Any, List

# AWS Libraries
from aws_cdk import CfnMapping, Duration, Stack, Tags, aws_rds, aws_ssm
from constructs import Construct

# Connected Mobility Solution on AWS
from .constructs.aurora_database import AuroraDatabaseConstruct
from .constructs.backstage_container import BackstageContainerConstruct
from .constructs.cognito import CognitoConstruct
from .constructs.load_balancer import LoadBalancerConstruct
from .constructs.module_integration import ModuleInputsConstruct
from .constructs.route53 import Route53Construct
from .lib.cms_common.config.resource_names import ResourceName
from .lib.cms_common.config.stack_inputs import (
    S3AssetConfigInputs,
    SolutionConfigInputs,
)
from .lib.cms_common.constructs.app_unique_id import AppUniqueId
from .lib.cms_common.constructs.cdk_lambda_vpc_config_construct import (
    CDKLambdasVpcConfigConstruct,
)
from .lib.cms_common.constructs.vpc_construct import VpcConstruct


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

        CfnMapping(
            self,
            "Solution",
            mapping={
                "AssetsConfig": {
                    "S3AssetBucketName": s3_asset_bucket_name,
                    "S3AssetKeyPrefix": s3_asset_config_inputs.object_key_prefix,
                },
            },
        )

        module_inputs = ModuleInputsConstruct(
            self,
            "module-inputs-construct",
            solution_config_inputs=solution_config_inputs,
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
            simple_name=True,
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
    def __init__(  # pylint: disable=R0914
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

        # Workaround for issue w/ SSM tokenization failing on lookup of IHostedZone
        route53_hosted_zone_name = os.environ["ROUTE53_HOSTED_ZONE_NAME"]
        route53_base_domain = os.environ["ROUTE53_BASE_DOMAIN"]

        route53_construct = Route53Construct(
            self,
            "route53-construct",
            route53_hosted_zone_name=route53_hosted_zone_name,
            route53_base_domain=route53_base_domain,
        )

        aurora_database_construct = AuroraDatabaseConstruct(
            self,
            "aurora-database-construct",
            vpc=vpc_construct.vpc,  # type: ignore[arg-type]
            isolated_subnets=vpc_construct.isolated_subnet_selection,
            credentials_secret_name=f"{module_inputs.acdp_config_ssm_prefix_with_slash_prefix}/backstage/db_credentials",
            cluster_engine=aws_rds.DatabaseClusterEngine.aurora_postgres(
                version=aws_rds.AuroraPostgresEngineVersion.VER_13_9
            ),
            rotation_interval_days=Duration.days(90),
        )

        cognito_construct = CognitoConstruct(
            self,
            "cognito-construct",
            admin_user=module_inputs.admin_user,
            email_invite_user_pool_name="Connected Mobility Solution - Backstage",
            route53_construct=route53_construct,
        )

        backstage_container_construct = BackstageContainerConstruct(
            self,
            "backstage-container-construct",
            module_inputs=module_inputs,
            cognito_construct=cognito_construct,
            postgres_database_construct=aurora_database_construct,
            vpc=vpc_construct.vpc,  # type: ignore[arg-type]
            private_subnets=vpc_construct.private_subnet_selection,
            route53_construct=route53_construct,
        )

        LoadBalancerConstruct(
            self,
            "load-balancer-construct",
            backstage_container_construct=backstage_container_construct,
            route53_construct=route53_construct,
            cognito_construct=cognito_construct,
            vpc=vpc_construct.vpc,  # type: ignore[arg-type]
            public_subnets=vpc_construct.public_subnet_selection,
        )
