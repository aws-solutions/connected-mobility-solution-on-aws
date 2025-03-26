# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
from os.path import abspath, dirname
from typing import Any

# AWS Libraries
from aws_cdk import Aws, CfnMapping, CfnOutput, Stack, Tags
from constructs import Construct

# CMS Common Library
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
from ..handlers.custom_resource.function.lib.data_sources import GrafanaDataSourceType
from .constructs.athena_data_source import AthenaDataSourceConstruct
from .constructs.grafana_alerts import GrafanaAlertsConstruct
from .constructs.grafana_api_key import GrafanaApiKeyConstruct
from .constructs.grafana_dashboard import GrafanaDashboardConstruct
from .constructs.grafana_plugins import GrafanaPluginsConstruct
from .constructs.grafana_workspace import GrafanaWorkspaceConstruct
from .constructs.module_integration import ModuleInputsConstruct, ModuleOutputsConstruct
from .constructs.process_alerts import ProcessAlertsConstruct
from .constructs.provision_alerts import ProvisionAlertsConstruct
from .constructs.s3_to_grafana import S3ToGrafanaConstruct


class CmsEVBatteryHealthStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        solution_config_inputs: SolutionConfigInputs,
        s3_asset_config_inputs: S3AssetConfigInputs,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

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

        self.ev_battery_health_construct = CmsEVBatteryHealthConstruct(
            self,
            "cms-ev-battery-health",
            solution_config_inputs=solution_config_inputs,
            module_inputs_construct=module_inputs_construct,
        )
        self.ev_battery_health_construct.node.add_dependency(
            register_module_with_app_unique_id
        )

        Tags.of(self.ev_battery_health_construct).add(
            "Solutions:DeploymentUUID", deployment_uuid
        )


class CmsEVBatteryHealthConstruct(Construct):
    DASHBOARD_S3_OBJECT_KEY_PREFIX: str = "cms/dashboards/"
    ALERTS_S3_OBJECT_KEY_PREFIX: str = "cms/alerts/"
    GRAFANA_API_KEY_EXPIRATION_DAYS: int = 30

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        solution_config_inputs: SolutionConfigInputs,
        module_inputs_construct: ModuleInputsConstruct,
    ) -> None:
        super().__init__(scope, construct_id)

        vpc_construct = VpcConstruct(
            self, "vpc-construct", vpc_config=module_inputs_construct.vpc_config
        )

        self.cdk_lambdas_vpc_construct = CDKLambdasVpcConfigConstruct(
            self,
            "cdk-lambdas-vpc-construct",
            vpc_construct=vpc_construct,
            subnets=module_inputs_construct.vpc_config.private_subnets,
        )

        lambda_dependencies = LambdaDependenciesConstruct(
            self,
            "cms-ev-dependency-layer-construct",
            pipfile_lock_dir=dirname(dirname(dirname(abspath(__file__)))),
            dependency_layer_path=f"{os.getcwd()}/deployment/dist/lambda/cms_ev_battery_health_dependency_layer",
        )

        custom_resource_lambda = CustomResourceLambdaConstruct(
            self,
            "cms-ev-custom-resource-lambda-construct",
            dependency_layer=lambda_dependencies.dependency_layer,
            unique_id=module_inputs_construct.app_unique_id,
            name=solution_config_inputs.module_short_name,
            asset_path=f"{os.getcwd()}/deployment/dist/lambda/custom_resource.zip",
            user_agent_string=solution_config_inputs.get_user_agent_string(),
            vpc_construct=vpc_construct,
        )

        grafana_workspace = GrafanaWorkspaceConstruct(
            self,
            "cms-ev-grafana-workspace-construct",
            app_unique_id=module_inputs_construct.app_unique_id,
            data_sources=["ATHENA"],
            notification_destinations=["SNS"],
            vpc_construct=vpc_construct,
            solution_config_inputs=solution_config_inputs,
        )

        grafana_api_key = GrafanaApiKeyConstruct(
            self,
            "cms-ev-grafana-api-key-construct",
            app_unique_id=module_inputs_construct.app_unique_id,
            solution_config_inputs=solution_config_inputs,
            dependency_layer=lambda_dependencies.dependency_layer,
            grafana_workspace_endpoint=grafana_workspace.workspace.attr_endpoint,
            grafana_workspace_id=grafana_workspace.workspace.attr_id,
            custom_resource_lambda_construct=custom_resource_lambda,
            grafana_api_key_expiration_days=self.GRAFANA_API_KEY_EXPIRATION_DAYS,
            vpc_construct=vpc_construct,
        )

        GrafanaPluginsConstruct(
            self,
            "cms-ev-install-plugins-construct",
            grafana_workspace_endpoint=grafana_workspace.workspace.attr_endpoint,
            grafana_api_key_construct=grafana_api_key,
            custom_resource_lambda_construct=custom_resource_lambda,
        )

        athena_data_source = AthenaDataSourceConstruct(
            self,
            "cms-ev-athena-data-source-construct",
            athena_data_source_properties=module_inputs_construct.athena_data_source_properties,
            grafana_api_key_construct=grafana_api_key,
            grafana_workspace_construct=grafana_workspace,
            custom_resource_lambda_construct=custom_resource_lambda,
        )

        s3_to_grafana = S3ToGrafanaConstruct(
            self,
            "cms-ev-s3-to-grafana-construct",
            module_inputs=module_inputs_construct,
            solution_config_inputs=solution_config_inputs,
            dependency_layer=lambda_dependencies.dependency_layer,
            grafana_api_key_secret_arn=grafana_api_key.secret.secret_arn,
            grafana_workspace_endpoint=grafana_workspace.workspace.attr_endpoint,
            dashboard_s3_object_key_prefix=self.DASHBOARD_S3_OBJECT_KEY_PREFIX,
            alerts_s3_object_key_prefix=self.ALERTS_S3_OBJECT_KEY_PREFIX,
            vpc_construct=vpc_construct,
        )

        grafana_dashboard = GrafanaDashboardConstruct(
            self,
            "cms-ev-grafana-dashboard-construct",
            grafana_s3_bucket_name=s3_to_grafana.grafana_assets_bucket.bucket.bucket_name,
            grafana_s3_bucket_arn=s3_to_grafana.grafana_assets_bucket.bucket.bucket_arn,
            data_sources={
                GrafanaDataSourceType.ATHENA.value: {
                    "data_source": athena_data_source.data_source.get_att("datasource"),
                    "athena_table": module_inputs_construct.athena_data_source_properties.glue_table_name,
                },
            },
            custom_resource_lambda_construct=custom_resource_lambda,
            dashboard_s3_object_key_prefix=self.DASHBOARD_S3_OBJECT_KEY_PREFIX,
        )
        grafana_dashboard.node.add_dependency(athena_data_source)

        provision_alerts = ProvisionAlertsConstruct(
            self,
            "cms-ev-provision-alerts-construct",
            app_unique_id=module_inputs_construct.app_unique_id,
            solution_config_inputs=solution_config_inputs,
            custom_resource_lambda_construct=custom_resource_lambda,
            dependency_layer=lambda_dependencies.dependency_layer,
            grafana_workspace_id=grafana_workspace.workspace.attr_id,
            vpc_construct=vpc_construct,
        )

        process_alerts = ProcessAlertsConstruct(
            self,
            "cms-ev-process-alerts-construct",
            app_unique_id=module_inputs_construct.app_unique_id,
            solution_config_inputs=solution_config_inputs,
            dependency_layer=lambda_dependencies.dependency_layer,
            grafana_api_key_secret_arn=grafana_api_key.secret.secret_arn,
            grafana_workspace_construct=grafana_workspace,
            custom_resource_lambda_construct=custom_resource_lambda,
            identity_provider_id=module_inputs_construct.identity_provider_id,
            alerts_publish_endpoint_url=module_inputs_construct.alerts_publish_endpoint_url,
            vpc_construct=vpc_construct,
        )
        process_alerts.node.add_dependency(provision_alerts)

        grafana_alerts = GrafanaAlertsConstruct(
            self,
            "cms-ev-grafana-alerts-construct",
            grafana_s3_bucket_name=s3_to_grafana.grafana_assets_bucket.bucket.bucket_name,
            grafana_s3_bucket_arn=s3_to_grafana.grafana_assets_bucket.bucket.bucket_arn,
            data_sources={
                GrafanaDataSourceType.ATHENA.value: {
                    "data_source": athena_data_source.data_source.get_att("datasource"),
                    "athena_table": module_inputs_construct.athena_data_source_properties.glue_table_name,
                },
            },
            custom_resource_lambda_construct=custom_resource_lambda,
            alerts_s3_object_key_prefix=self.ALERTS_S3_OBJECT_KEY_PREFIX,
        )
        grafana_alerts.node.add_dependency(provision_alerts)
        grafana_alerts.node.add_dependency(athena_data_source)

        ModuleOutputsConstruct(
            self,
            "cms-ev-module-outputs-construct",
            app_unique_id=module_inputs_construct.app_unique_id,
            solution_config_inputs=solution_config_inputs,
            grafana_endpoint=grafana_workspace.workspace.attr_endpoint,
        )

        CfnOutput(
            self,
            "cms-ev-battery-health-grafana-workspace-url",
            description="CMS EV Battery Health Grafana workspace URL.",
            value=f"https://{grafana_workspace.workspace.attr_endpoint}",
        )
