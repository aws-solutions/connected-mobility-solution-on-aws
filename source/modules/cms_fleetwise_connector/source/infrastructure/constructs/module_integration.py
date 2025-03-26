# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from dataclasses import dataclass

# Third Party Libraries
from attrs import define

# AWS Libraries
from aws_cdk import CfnOutput, CfnParameter, Stack, aws_ssm
from constructs import Construct

# CMS Common Library
from cms_common.config.metrics import OperationalMetricsInput
from cms_common.config.resource_names import ResourceName, ResourcePrefix
from cms_common.config.ssm import resolve_ssm_parameter
from cms_common.config.stack_inputs import SolutionConfigInputs
from cms_common.constructs.app_unique_id import AppUniqueId
from cms_common.constructs.vpc_construct import create_vpc_config, get_vpc_name
from cms_common.resource_names.module_short_names import CMSModuleShortNames

MINUTES_IN_A_WEEK = 10080


@dataclass(frozen=True)
class TelemetryBucketInputs:
    bucket_arn: str
    bucket_name: str


@define(auto_attribs=True, frozen=True)
class ModuleConfigInputs:
    app_unique_id: str
    module_ssm_prefix: str
    fleetwise_vehicle_vin_attribute_name: str
    timestream_to_s3_unload_interval_minutes: int | float
    timestream_unload_s3_prefix_path: str
    glue_crawler_cron_expression: str


@define(auto_attribs=True, frozen=True)
class TimestreamOutputs:
    database_name: str
    database_arn: str
    table_name: str
    table_arn: str
    region: str
    timestream_key_arn: str


class ModuleInputsConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        solution_config_inputs: SolutionConfigInputs,
    ) -> None:
        super().__init__(scope, construct_id)

        app_unique_id = AppUniqueId.create_cfn_parameter(Stack.of(self))

        self.vpc_config = create_vpc_config(
            vpc_name=get_vpc_name(self, app_unique_id=app_unique_id)
        )

        fleetwise_vehicle_vin_attribute_name = CfnParameter(
            Stack.of(self),
            "FleetwiseVehicleVinAttributeName",
            type="String",
            default="VehicleVIN",
            description="Vehicle Attribute Name for the VIN configured for each vehicle used in FleetWise",
            allowed_pattern=r"^[a-zA-Z0-9:_]+$",
            constraint_description="FleetWise attribute names and path can have up to 150 characters. Valid characters: a-z, A-Z, 0-9, : (colon), and _ (underscore)",
            min_length=1,
            max_length=150,
        ).value_as_string

        timestream_to_s3_unload_interval_minutes = CfnParameter(
            Stack.of(self),
            "TimestreamToS3UnloadIntervalMinutes",
            type="Number",
            default="15",
            description="The rate in minutes that the unload step function is run",
            min_value=1,
            max_value=MINUTES_IN_A_WEEK,
            constraint_description=f"Must be between 1 minute and {MINUTES_IN_A_WEEK} minutes (1 week)",
        ).value_as_number

        glue_crawler_cron_expression = CfnParameter(
            Stack.of(self),
            "GlueCrawlerCronExpression",
            type="String",
            default="cron(0 0/1 * * ? *)",
            description="The CRON expression to define how often the Glue Crawler runs.",
        ).value_as_string

        module_ssm_prefix = ResourcePrefix.slash_separated(
            app_unique_id=app_unique_id,
            module_name=solution_config_inputs.module_short_name,
        )

        self.module_config_inputs = ModuleConfigInputs(
            app_unique_id=app_unique_id,
            module_ssm_prefix=module_ssm_prefix,
            fleetwise_vehicle_vin_attribute_name=fleetwise_vehicle_vin_attribute_name,
            timestream_to_s3_unload_interval_minutes=timestream_to_s3_unload_interval_minutes,
            timestream_unload_s3_prefix_path="fleetwise_timestream_to_s3",
            glue_crawler_cron_expression=glue_crawler_cron_expression,
        )

        self.operational_metrics = OperationalMetricsInput.from_app_unique_id(
            app_unique_id=app_unique_id
        )

        connect_store_module_ssm_prefix_with_leading_slash = (
            ResourcePrefix.slash_separated(
                app_unique_id=app_unique_id,
                module_name=CMSModuleShortNames.CONNECT_STORE,
                leading_slash=True,
            )
        )
        self.telemetry_bucket = TelemetryBucketInputs(
            bucket_arn=resolve_ssm_parameter(
                parameter_name=ResourceName.slash_separated(
                    prefix=connect_store_module_ssm_prefix_with_leading_slash,
                    name="s3-storage-bucket/arn",
                )
            ),
            bucket_name=resolve_ssm_parameter(
                parameter_name=ResourceName.slash_separated(
                    prefix=connect_store_module_ssm_prefix_with_leading_slash,
                    name="s3-storage-bucket/name",
                )
            ),
        )


class ModuleOutputsConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        module_config: ModuleConfigInputs,
        timestream: TimestreamOutputs,
        fleetwise_execution_role_arn: str,
    ) -> None:
        super().__init__(scope, construct_id)

        module_ssm_prefix_with_leading_slash = f"/{module_config.module_ssm_prefix}"

        # SSM Parameters
        self.timestream_database_name = aws_ssm.StringParameter(
            self,
            "ssm-timestream-database-name",
            string_value=timestream.database_name,
            description="Name of the Timestream Database where FleeWise data is stored",
            parameter_name=ResourceName.slash_separated(
                prefix=module_ssm_prefix_with_leading_slash,
                name="timestream/database/name",
            ),
            simple_name=False,
        )
        self.timestream_database_arn = aws_ssm.StringParameter(
            self,
            "ssm-timestream-database-arn",
            string_value=timestream.database_arn,
            description="Arn of the Timestream Database where FleeWise data is stored",
            parameter_name=ResourceName.slash_separated(
                prefix=module_ssm_prefix_with_leading_slash,
                name="timestream/database/arn",
            ),
            simple_name=False,
        )
        self.timestream_table_name = aws_ssm.StringParameter(
            self,
            "ssm-timestream-table-name",
            string_value=timestream.table_name,
            description="Name of the Timestream Table where FleetWise data is stored",
            parameter_name=ResourceName.slash_separated(
                prefix=module_ssm_prefix_with_leading_slash,
                name="timestream/table/name",
            ),
            simple_name=False,
        )
        self.timestream_table_arn = aws_ssm.StringParameter(
            self,
            "ssm-timestream-table-arn",
            string_value=timestream.table_arn,
            description="Arn of the Timestream Table where FleetWise data is stored",
            parameter_name=ResourceName.slash_separated(
                prefix=module_ssm_prefix_with_leading_slash, name="timestream/table/arn"
            ),
            simple_name=False,
        )
        self.timestream_database_region = aws_ssm.StringParameter(
            self,
            "ssm-timestream-database-region",
            string_value=timestream.region,
            description="Region of the Timestream Service where FleetWise data is stored",
            parameter_name=ResourceName.slash_separated(
                prefix=module_ssm_prefix_with_leading_slash, name="timestream/region"
            ),
            simple_name=False,
        )
        self.timestream_kms_key_arn = aws_ssm.StringParameter(
            self,
            "ssm-timestream-database-key-arn",
            string_value=timestream.timestream_key_arn,
            description="Arn of KMS key for the Timestream Database where FleetWise data is stored",
            parameter_name=ResourceName.slash_separated(
                prefix=module_ssm_prefix_with_leading_slash,
                name="timestream/database/key-arn",
            ),
            simple_name=False,
        )

        self.fleetwise_execution_role_arn = aws_ssm.StringParameter(
            self,
            "ssm-fleetwise-execution-role-arn",
            string_value=fleetwise_execution_role_arn,
            description="Arn of IAM Role to use for executing FleetWise Campaigns that store data in FleetWise",
            parameter_name=ResourceName.slash_separated(
                prefix=module_ssm_prefix_with_leading_slash,
                name="fleetwise/execution-role/arn",
            ),
            simple_name=False,
        )

        self.fleetwise_vehicle_vin_attribute_name_parameter = aws_ssm.StringParameter(
            self,
            "ssm-fleetwise-vehicle-vin-attribute-name",
            string_value=module_config.fleetwise_vehicle_vin_attribute_name,
            description="FleetWise Vehicle VIN Attribute Name",
            parameter_name=ResourceName.slash_separated(
                prefix=module_ssm_prefix_with_leading_slash,
                name="fleetwise/vehicle/vin-attribute-name",
            ),
            simple_name=False,
        )

        # Cfn Outputs
        CfnOutput(
            self,
            "output-timestream-database-name",
            description="Timestream Database Name for the FleetWise Connector",
            value=timestream.database_name,
        )

        CfnOutput(
            self,
            "output-timestream-table-name",
            description="Timestream Table Name for the FleetWise Connector",
            value=timestream.table_name,
        )

        CfnOutput(
            self,
            "output-timestream-table-arn",
            description="Timestream Table ARN for the FleetWise Connector",
            value=timestream.table_arn,
        )
