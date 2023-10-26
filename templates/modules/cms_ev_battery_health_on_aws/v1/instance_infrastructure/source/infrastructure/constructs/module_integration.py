# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from dataclasses import dataclass

# Third Party Libraries
from aws_cdk import aws_ssm
from constructs import Construct

# Connected Mobility Solution on AWS
from ...config.constants import EVBatteryHealthConstants


@dataclass(frozen=True)
class AthenaDataSourceProperties:
    athena_data_storage_bucket_arn: str
    athena_data_storage_bucket_key_arn: str
    athena_workgroup_name: str
    athena_results_bucket_arn: str
    athena_results_bucket_key_arn: str
    glue_catalog_name: str
    glue_database_name: str
    glue_table_name: str
    glue_registry_name: str
    glue_schema_arn: str


@dataclass(frozen=True)
class ServiceAuthenticationParameters:
    user_pool_domain: str
    user_pool_region: str
    client_id: str
    client_secret_arn: str
    caller_scope: str
    resource_server_id: str


class ModuleInputsConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
    ) -> None:
        super().__init__(scope, construct_id)

        telemetry_glue_data_catalog_name = aws_ssm.StringParameter.from_string_parameter_attributes(
            self,
            "ssm-glue-data-catalog-name",
            parameter_name=f"/{EVBatteryHealthConstants.STAGE}/cms/telemetry/glue-data-catalog/name",
        )
        telemetry_glue_database_name = aws_ssm.StringParameter.from_string_parameter_attributes(
            self,
            "glue-database-name",
            parameter_name=f"/{EVBatteryHealthConstants.STAGE}/cms/telemetry/glue-database/name",
        )
        telemetry_glue_table_name = aws_ssm.StringParameter.from_string_parameter_attributes(
            self,
            "ssm-glue-table-name",
            parameter_name=f"/{EVBatteryHealthConstants.STAGE}/cms/telemetry/glue-table/name",
        )
        telemetry_glue_registry_name = aws_ssm.StringParameter.from_string_parameter_attributes(
            self,
            "ssm-glue-registry-name",
            parameter_name=f"/{EVBatteryHealthConstants.STAGE}/cms/telemetry/glue-registry/name",
        )
        telemetry_glue_schema_arn = aws_ssm.StringParameter.from_string_parameter_attributes(
            self,
            "ssm-glue-schema-arn",
            parameter_name=f"/{EVBatteryHealthConstants.STAGE}/cms/telemetry/glue-schema/arn",
        )
        telemetry_athena_workgroup_name = aws_ssm.StringParameter.from_string_parameter_attributes(
            self,
            "ssm-athena-workgroup-name",
            parameter_name=f"/{EVBatteryHealthConstants.STAGE}/cms/api/athena-workgroup/name",
        )
        telemetry_athena_results_bucket_arn = aws_ssm.StringParameter.from_string_parameter_attributes(
            self,
            "ssm-athena-results-bucket-arn",
            parameter_name=f"/{EVBatteryHealthConstants.STAGE}/cms/api/athena-result-bucket/arn",
        )
        telemetry_athena_results_bucket_key_arn = aws_ssm.StringParameter.from_string_parameter_attributes(
            self,
            "ssm-athena-results-bucket-key-arn",
            parameter_name=f"/{EVBatteryHealthConstants.STAGE}/cms/api/athena-result-bucket/key-arn",
        )
        telemetry_storage_bucket_arn = aws_ssm.StringParameter.from_string_parameter_attributes(
            self,
            "ssm-storage-bucket-arn",
            parameter_name=f"/{EVBatteryHealthConstants.STAGE}/cms/telemetry/s3-storage-bucket/arn",
        )
        telemetry_storage_bucket_key_arn = aws_ssm.StringParameter.from_string_parameter_attributes(
            self,
            "ssm-storage-bucket-key-arn",
            parameter_name=f"/{EVBatteryHealthConstants.STAGE}/cms/telemetry/s3-storage-bucket/key-arn",
        )

        self.athena_data_source_properties = AthenaDataSourceProperties(
            athena_data_storage_bucket_arn=telemetry_storage_bucket_arn.string_value,
            athena_data_storage_bucket_key_arn=telemetry_storage_bucket_key_arn.string_value,
            athena_workgroup_name=telemetry_athena_workgroup_name.string_value,
            athena_results_bucket_arn=telemetry_athena_results_bucket_arn.string_value,
            athena_results_bucket_key_arn=telemetry_athena_results_bucket_key_arn.string_value,
            glue_catalog_name=telemetry_glue_data_catalog_name.string_value,
            glue_database_name=telemetry_glue_database_name.string_value,
            glue_registry_name=telemetry_glue_registry_name.string_value,
            glue_schema_arn=telemetry_glue_schema_arn.string_value,
            glue_table_name=telemetry_glue_table_name.string_value,
        )

        authentication_service_client_id = aws_ssm.StringParameter.from_string_parameter_attributes(
            self,
            "ssm-authentication-service-client-id",
            parameter_name=f"/{EVBatteryHealthConstants.STAGE}/cms/authentication/service-client/id",
        )

        authentication_service_client_secret_arn = aws_ssm.StringParameter.from_string_parameter_attributes(
            self,
            "ssm-authentication-service-client-secret-arn",
            parameter_name=f"/{EVBatteryHealthConstants.STAGE}/cms/authentication/service-client-secret/secret-arn",
        )

        authentication_user_pool_domain = aws_ssm.StringParameter.from_string_parameter_attributes(
            self,
            "ssm-authentication-user-pool-domain",
            parameter_name=f"/{EVBatteryHealthConstants.STAGE}/cms/authentication/user-pool/domain-prefix",
        )

        authentication_user_pool_region = aws_ssm.StringParameter.from_string_parameter_attributes(
            self,
            "ssm-authentication-user-pool-region",
            parameter_name=f"/{EVBatteryHealthConstants.STAGE}/cms/authentication/user-pool/region",
        )

        authentication_resource_server_id = aws_ssm.StringParameter.from_string_parameter_attributes(
            self,
            "ssm-authentication-resource-server-id",
            parameter_name=f"/{EVBatteryHealthConstants.STAGE}/cms/authentication/resource-server/identifier",
        )

        authentication_service_caller_scope = aws_ssm.StringParameter.from_string_parameter_attributes(
            self,
            "ssm-authentication-service-caller-scope",
            parameter_name=f"/{EVBatteryHealthConstants.STAGE}/cms/authentication/service-caller-scope/name",
        )

        self.service_authentication_parameters = ServiceAuthenticationParameters(
            user_pool_domain=authentication_user_pool_domain.string_value,
            user_pool_region=authentication_user_pool_region.string_value,
            client_id=authentication_service_client_id.string_value,
            client_secret_arn=authentication_service_client_secret_arn.string_value,
            caller_scope=authentication_service_caller_scope.string_value,
            resource_server_id=authentication_resource_server_id.string_value,
        )

        self.alerts_publish_endpoint_url = aws_ssm.StringParameter.from_string_parameter_attributes(
            self,
            "ssm-alerts-publish-endpoint-url",
            parameter_name=f"/{EVBatteryHealthConstants.STAGE}/cms/alerts/publish-api/endpoint",
        )


class ModuleOutputsConstruct(Construct):
    def __init__(
        self, scope: Construct, construct_id: str, grafana_endpoint: str
    ) -> None:
        super().__init__(scope, construct_id)

        aws_ssm.StringParameter(
            self,
            "ssm-grafana-endpoint",
            string_value=grafana_endpoint,
            description="EV Battery Health Dashboard Grafana Endpoint",
            parameter_name=f"/{EVBatteryHealthConstants.STAGE}/cms/ev-battery-health/grafana-workspace-endpoint/url",
        )
