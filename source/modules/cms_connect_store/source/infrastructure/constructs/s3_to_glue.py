# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json
from dataclasses import dataclass
from typing import Any, Dict

# Third Party Libraries
from dataclass_type_validator import dataclass_validate  # type: ignore

# AWS Libraries
from aws_cdk import Stack, aws_glue, aws_s3
from constructs import Construct

# CMS Common Library
from cms_common.config.resource_names import ResourceName, ResourcePrefix
from cms_common.config.stack_inputs import SolutionConfigInputs


@dataclass_validate
@dataclass
class GlueResources:
    glue_table: aws_glue.CfnTable
    glue_schema: aws_glue.CfnSchema
    glue_database: aws_glue.CfnDatabase


class S3ToGlueConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_unique_id: str,
        schema_json: Dict[str, Any],
        default_registry_name: str,
        root_s3_bucket: aws_s3.Bucket,
        solution_config_inputs: SolutionConfigInputs,
    ) -> None:
        super().__init__(scope, construct_id)

        # Define schema in default registry.
        cfn_schema = aws_glue.CfnSchema(
            self,
            "vehicle-signal-specification-json-schema",
            compatibility="NONE",
            data_format="JSON",
            name=ResourceName.hyphen_separated(
                prefix=ResourcePrefix.hyphen_separated(
                    app_unique_id=app_unique_id,
                    module_name=solution_config_inputs.module_short_name,
                ),
                name="glue-schema",
            ),
            schema_definition=json.dumps(schema_json),
            # the properties below are optional
            checkpoint_version=aws_glue.CfnSchema.SchemaVersionProperty(
                is_latest=True,
                version_number=1,
            ),
            description="JSON schema for vehicle signal specification data. Vin is required for partitioning.",
            registry=aws_glue.CfnSchema.RegistryProperty(name=default_registry_name),
        )

        # Create database
        cfn_database = aws_glue.CfnDatabase(
            self,
            "iot-data-conversion-glue-database",
            catalog_id=Stack.of(self).account,
            database_input=aws_glue.CfnDatabase.DatabaseInputProperty(
                name=ResourceName.hyphen_separated(
                    prefix=ResourcePrefix.hyphen_separated(
                        app_unique_id=app_unique_id,
                        module_name=solution_config_inputs.module_short_name,
                    ),
                    name="iot-data-conversion-glue-database",
                ),
                description="This database holds reference table(s) for Kinesis Firehose",
            ),
        )
        # Create table
        cfn_table = aws_glue.CfnTable(
            self,
            "iot-main-stream-glue-schema-table",
            catalog_id=Stack.of(self).account,
            database_name=cfn_database.database_input.name,  # type: ignore [union-attr, arg-type]
            table_input=aws_glue.CfnTable.TableInputProperty(
                description="Main data stream for IoT Core reference table",
                name="iot-main-stream-glue-schema-table",
                storage_descriptor=aws_glue.CfnTable.StorageDescriptorProperty(
                    location=f"s3://{root_s3_bucket.bucket_name}/cms/data",
                    input_format="org.apache.hadoop.mapred.TextInputFormat",
                    output_format="org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat",
                    serde_info=aws_glue.CfnTable.SerdeInfoProperty(
                        serialization_library="org.openx.data.jsonserde.JsonSerDe",
                    ),
                    schema_reference=aws_glue.CfnTable.SchemaReferenceProperty(
                        schema_id=aws_glue.CfnTable.SchemaIdProperty(
                            registry_name=cfn_schema.registry.name,  # type: ignore [union-attr]
                            schema_name=cfn_schema.name,
                        ),
                        schema_version_number=1,
                    ),
                ),
            ),
        )
        cfn_table.add_dependency(cfn_schema)
        cfn_table.add_dependency(cfn_database)

        self.glue_resources = GlueResources(
            glue_table=cfn_table,
            glue_schema=cfn_schema,
            glue_database=cfn_database,
        )
