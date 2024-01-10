# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any

# Third Party Libraries
from aws_cdk import CfnOutput, Stack, Tags, aws_ssm
from constructs import Construct

# Connected Mobility Solution on AWS
from ..config.constants import EVBatteryHealthConstants
from ..handlers.custom_resource.lib.data_sources import GrafanaDataSourceType
from .constructs.app_registry import AppRegistryConstruct
from .constructs.athena_data_source import AthenaDataSourceConstruct
from .constructs.custom_resource_lambda import CustomResourceLambdaConstruct
from .constructs.grafana_alerts import GrafanaAlertsConstruct
from .constructs.grafana_api_key import GrafanaApiKeyConstruct
from .constructs.grafana_dashboard import GrafanaDashboardConstruct
from .constructs.grafana_plugins import GrafanaPluginsConstruct
from .constructs.grafana_workspace import GrafanaWorkspaceConstruct
from .constructs.lambda_dependency import LambdaDependenciesConstruct
from .constructs.module_integration import ModuleInputsConstruct, ModuleOutputsConstruct
from .constructs.process_alerts import ProcessAlertsConstruct
from .constructs.provision_alerts import ProvisionAlertsConstruct
from .constructs.s3_to_grafana import S3ToGrafanaConstruct


class CmsEVBatteryHealthOnAwsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        deployment_uuid = aws_ssm.StringParameter.from_string_parameter_name(
            self,
            "deployment-uuid",
            f"/{EVBatteryHealthConstants.STAGE}/cms/common/config/deployment-uuid",
        ).string_value

        ev_battery_health_construct = CmsEVBatteryHealthConstruct(
            self, "cms-ev-battery-health"
        )

        Tags.of(ev_battery_health_construct).add(
            "Solutions:DeploymentUUID", deployment_uuid
        )


class CmsEVBatteryHealthConstruct(Construct):
    def __init__(self, scope: Construct, construct_id: str) -> None:
        super().__init__(scope, construct_id)

        AppRegistryConstruct(
            self,
            "cms-ev-battery-health-app-registry",
            application_name=EVBatteryHealthConstants.APP_NAME,
            application_type=EVBatteryHealthConstants.APPLICATION_TYPE,
            solution_id=EVBatteryHealthConstants.SOLUTION_ID,
            solution_name=EVBatteryHealthConstants.SOLUTION_NAME,
            solution_version=EVBatteryHealthConstants.SOLUTION_VERSION,
        )

        module_inputs = ModuleInputsConstruct(self, "cms-ev-module-inputs-construct")

        lambda_dependencies = LambdaDependenciesConstruct(
            self,
            "cms-ev-lambda-dependencies-construct",
            dependency_layer_dir_name="ev_battery_dependency_layer",
        )

        custom_resource_lambda = CustomResourceLambdaConstruct(
            self,
            "cms-ev-custom-resource-lambda-construct",
            dependency_layer=lambda_dependencies.dependency_layer,
        )

        grafana_workspace = GrafanaWorkspaceConstruct(
            self,
            "cms-ev-grafana-workspace-construct",
            data_sources=["ATHENA"],
            notification_destinations=["SNS"],
        )

        grafana_api_key = GrafanaApiKeyConstruct(
            self,
            "cms-ev-grafana-api-key-construct",
            dependency_layer=lambda_dependencies.dependency_layer,
            grafana_workspace_endpoint=grafana_workspace.workspace.attr_endpoint,
            grafana_workspace_id=grafana_workspace.workspace.attr_id,
            custom_resource_lambda_construct=custom_resource_lambda,
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
            athena_data_source_properties=module_inputs.athena_data_source_properties,
            grafana_api_key_construct=grafana_api_key,
            grafana_workspace_construct=grafana_workspace,
            custom_resource_lambda_construct=custom_resource_lambda,
        )

        s3_to_grafana = S3ToGrafanaConstruct(
            self,
            "cms-ev-s3-to-grafana-construct",
            dependency_layer=lambda_dependencies.dependency_layer,
            grafana_api_key_secret_arn=grafana_api_key.secret.secret_arn,
            grafana_workspace_endpoint=grafana_workspace.workspace.attr_endpoint,
        )

        grafana_dashboard = GrafanaDashboardConstruct(
            self,
            "cms-ev-grafana-dashboard-construct",
            grafana_s3_bucket_name=s3_to_grafana.s3_bucket.bucket_name,
            grafana_s3_bucket_arn=s3_to_grafana.s3_bucket.bucket_arn,
            grafana_s3_bucket_key_arn=s3_to_grafana.s3_key.key_arn,
            data_sources={
                GrafanaDataSourceType.ATHENA.value: {
                    "data_source": athena_data_source.data_source.get_att("datasource"),
                    "athena_table": module_inputs.athena_data_source_properties.glue_table_name,
                },
            },
            custom_resource_lambda_construct=custom_resource_lambda,
        )
        grafana_dashboard.node.add_dependency(athena_data_source)

        provision_alerts = ProvisionAlertsConstruct(
            self,
            "cms-ev-provision-alerts-construct",
            custom_resource_lambda_construct=custom_resource_lambda,
            dependency_layer=lambda_dependencies.dependency_layer,
            grafana_workspace_id=grafana_workspace.workspace.attr_id,
        )

        process_alerts = ProcessAlertsConstruct(
            self,
            "cms-ev-process-alerts-construct",
            dependency_layer=lambda_dependencies.dependency_layer,
            grafana_api_key_secret_arn=grafana_api_key.secret.secret_arn,
            grafana_workspace_construct=grafana_workspace,
            custom_resource_lambda_construct=custom_resource_lambda,
            service_authentication_parameters=module_inputs.service_authentication_parameters,
            alerts_publish_endpoint_url=module_inputs.alerts_publish_endpoint_url.string_value,
        )
        process_alerts.node.add_dependency(provision_alerts)

        grafana_alerts = GrafanaAlertsConstruct(
            self,
            "cms-ev-grafana-alerts-construct",
            grafana_s3_bucket_name=s3_to_grafana.s3_bucket.bucket_name,
            grafana_s3_bucket_arn=s3_to_grafana.s3_bucket.bucket_arn,
            grafana_s3_bucket_key_arn=s3_to_grafana.s3_key.key_arn,
            data_sources={
                GrafanaDataSourceType.ATHENA.value: {
                    "data_source": athena_data_source.data_source.get_att("datasource"),
                    "athena_table": module_inputs.athena_data_source_properties.glue_table_name,
                },
            },
            custom_resource_lambda_construct=custom_resource_lambda,
        )
        grafana_alerts.node.add_dependency(provision_alerts)
        grafana_alerts.node.add_dependency(athena_data_source)

        ModuleOutputsConstruct(
            self,
            "cms-ev-module-outputs-construct",
            grafana_endpoint=grafana_workspace.workspace.attr_endpoint,
        )

        CfnOutput(
            self,
            "cms-ev-battery-health-grafana-workspace-url",
            description="CMS EV Battery Health Grafana workspace URL.",
            value=f"https://{grafana_workspace.workspace.attr_endpoint}",
        )
