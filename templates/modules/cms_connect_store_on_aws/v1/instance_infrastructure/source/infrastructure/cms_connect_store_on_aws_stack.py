# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import dataclasses
import json
from os.path import dirname, realpath
from typing import Any

# Third Party Libraries
from aws_cdk import (
    ArnFormat,
    Stack,
    Tags,
    aws_glue,
    aws_iam,
    aws_iot,
    aws_kinesisfirehose,
    aws_kms,
    aws_logs,
    aws_s3,
    aws_ssm,
)
from constructs import Construct
from dataclass_type_validator import dataclass_validate  # type: ignore

# Connected Mobility Solution on AWS
from ..config.constants import ConnectStoreConstants
from ..infrastructure.constructs.app_registry import AppRegistryConstruct
from .constructs.alerts_construct import AlertsConstruct
from .constructs.lambda_dependencies import LambdaDependenciesConstruct
from .constructs.module_integration import ModuleInputsConstruct


@dataclass_validate
@dataclasses.dataclass(frozen=True)
class GlueDBResources:
    glue_database: aws_glue.CfnDatabase
    glue_table: aws_glue.CfnTable
    glue_schema: aws_glue.CfnSchema


class CmsConnectStoreOnAwsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)
        deployment_uuid = aws_ssm.StringParameter.from_string_parameter_name(
            self,
            "deployment-uuid",
            f"/{ConnectStoreConstants.STAGE}/cms/common/config/deployment-uuid",
        ).string_value
        connect_store_construct = CmsConnectStoreConstruct(
            self, "connect-store", account=self.account
        )
        Tags.of(connect_store_construct).add(
            "Solutions:DeploymentUUID", deployment_uuid
        )


class CmsConnectStoreConstruct(Construct):
    default_registry_name = "default-registry"  # This name is pre-specified by Glue, and allows the automatic creation of a registry
    primary_iot_core_query = (
        "SELECT * FROM 'cms/data/#'"  # primary topic prefix to listen for the data
    )
    vehicle_notifications_iot_core_query = "SELECT * from 'cms/notification/#'"

    def __init__(self, scope: Construct, construct_id: str, account: str) -> None:
        super().__init__(scope, construct_id)

        AppRegistryConstruct(
            self,
            "cms-connect-and-store-app-registry",
            application_name=ConnectStoreConstants.APP_NAME,
            application_type=ConnectStoreConstants.APPLICATION_TYPE,
            solution_id=ConnectStoreConstants.SOLUTION_ID,
            solution_name=ConnectStoreConstants.SOLUTION_NAME,
            solution_version=ConnectStoreConstants.SOLUTION_VERSION,
        )

        self.module_inputs = ModuleInputsConstruct(
            self, "connect-store-module-inputs-construct"
        )

        server_access_logs_key = aws_kms.Key(
            self,
            "connect-store-server-access-root-s3-key",
            enable_key_rotation=True,
        )

        self.dependency_layer_construct = LambdaDependenciesConstruct(
            self,
            "connect-store-lambda-dependencies",
            dependency_layer_dir_name="connect_store_dependency_layer",
        )

        self.alerts_construct = AlertsConstruct(
            self,
            "connect-store-alerts-construct",
            dependency_layer=self.dependency_layer_construct.dependency_layer,
            alerts_publish_endpoint_url=self.module_inputs.alerts_publish_endpoint_url.string_value,
            service_authentication_parameters=self.module_inputs.service_authentication_parameters,
        )

        server_access_logs_bucket = aws_s3.Bucket(
            self,
            "connect-store-server-access-logs-bucket",
            enforce_ssl=True,
            block_public_access=aws_s3.BlockPublicAccess.BLOCK_ALL,
            versioned=True,
            encryption=aws_s3.BucketEncryption.KMS,
            encryption_key=server_access_logs_key,
        )

        root_s3_key = aws_kms.Key(
            self,
            "connect-store-root-s3-key",
            enable_key_rotation=True,
        )

        self.root_s3 = aws_s3.Bucket(
            self,
            "connect-store-root-s3",
            enforce_ssl=True,
            encryption_key=root_s3_key,
            encryption=aws_s3.BucketEncryption.KMS,
            server_access_logs_bucket=server_access_logs_bucket,
            block_public_access=aws_s3.BlockPublicAccess.BLOCK_ALL,
            versioned=True,
        )

        glue_db_resources = self.create_glue_table()
        self.glue_database = glue_db_resources.glue_database
        self.glue_table = glue_db_resources.glue_table
        self.glue_schema = glue_db_resources.glue_schema
        self.kinesis_firehouse_stream = self.create_firehose_streams()
        self.setup_iot_core_rules()

        # Export SSM parameters for resources created in this stack
        aws_ssm.StringParameter(
            self,
            "ssm-telemetry-glue-data-catalog",
            description="The Glue data catalog in which the table is to be created.",
            parameter_name=f"/{ConnectStoreConstants.STAGE}/cms/telemetry/glue-data-catalog/name",
            string_value="AwsDataCatalog",
        )
        aws_ssm.StringParameter(
            self,
            "ssm-telemetry-glue-database",
            description="The Glue database in which the telemetry table is stored.",
            parameter_name=f"/{ConnectStoreConstants.STAGE}/cms/telemetry/glue-database/name",
            string_value=self.glue_database.database_input.name,  # type: ignore
        )
        aws_ssm.StringParameter(
            self,
            "ssm-telemetry-glue-table",
            description="The Glue table which references to the stored telemetry data.",
            parameter_name=f"/{ConnectStoreConstants.STAGE}/cms/telemetry/glue-table/name",
            string_value=self.glue_table.table_input.name,  # type: ignore
        )
        aws_ssm.StringParameter(
            self,
            "ssm-glue-schema-arn",
            string_value=self.glue_schema.attr_arn,
            description="CMS Connect and Store AWS Glue Schema Arn",
            parameter_name=f"/{ConnectStoreConstants.STAGE}/cms/telemetry/glue-schema/arn",
        )
        aws_ssm.StringParameter(
            self,
            "ssm-glue-registry-name",
            string_value=self.glue_schema.registry.name,  # type: ignore
            description="CMS Connect and Store AWS Glue Registry Name",
            parameter_name=f"/{ConnectStoreConstants.STAGE}/cms/telemetry/glue-registry/name",
        )
        aws_ssm.StringParameter(
            self,
            "ssm-telemetry-storage-bucket-region",
            description="The region of the S3 bucket in which the telemetry data is stored.",
            parameter_name=f"/{ConnectStoreConstants.STAGE}/cms/telemetry/s3-storage-bucket/region",
            string_value=Stack.of(self).region,
        )
        aws_ssm.StringParameter(
            self,
            "ssm-telemetry-storage-bucket-name",
            description="The name of the S3 bucket in which the telemetry data is stored.",
            parameter_name=f"/{ConnectStoreConstants.STAGE}/cms/telemetry/s3-storage-bucket/name",
            string_value=self.root_s3.bucket_name,
        )
        aws_ssm.StringParameter(
            self,
            "ssm-telemetry-storage-bucket-arn",
            description="The ARN of the S3 bucket in which the telemetry data is stored.",
            parameter_name=f"/{ConnectStoreConstants.STAGE}/cms/telemetry/s3-storage-bucket/arn",
            string_value=self.root_s3.bucket_arn,
        )
        aws_ssm.StringParameter(
            self,
            "ssm-telemetry-storage-bucket-key-arn",
            description="The ARN of the encryption key for the S3 bucket in which the telemetry data is stored.",
            parameter_name=f"/{ConnectStoreConstants.STAGE}/cms/telemetry/s3-storage-bucket/key-arn",
            string_value=root_s3_key.key_arn,
        )

    def create_glue_table(self) -> GlueDBResources:
        """
        For data conversion from JSON to Apache Parquet,
        Load conversion schema and setup AWS glue table.
        """

        # Load VSS schema from file.
        with open(
            f"{dirname(realpath(__file__))}/assets/vss.json",
            encoding="utf-8",
        ) as file:
            raw_vss_schema = json.load(file)

        # Define schema in default registry.
        cfn_schema = aws_glue.CfnSchema(
            self,
            "vehicle-signal-specification-json-schema",
            compatibility="NONE",
            data_format="JSON",
            name=f"{ConnectStoreConstants.APP_NAME}-glue-schema",
            schema_definition=json.dumps(raw_vss_schema),
            # the properties below are optional
            checkpoint_version=aws_glue.CfnSchema.SchemaVersionProperty(
                is_latest=True,
                version_number=1,
            ),
            description="JSON schema for vehicle signal specification data. Vin is required for partitioning.",
            registry=aws_glue.CfnSchema.RegistryProperty(
                name=self.default_registry_name
            ),
        )

        # Create database
        cfn_database = aws_glue.CfnDatabase(
            self,
            "iot-data-conversion-glue-database",
            catalog_id=Stack.of(self).account,
            database_input=aws_glue.CfnDatabase.DatabaseInputProperty(
                name="iot-data-conversion-glue-database",
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
                    location=f"s3://{self.root_s3.bucket_name}/cms/data",
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

        return GlueDBResources(
            glue_database=cfn_database, glue_table=cfn_table, glue_schema=cfn_schema
        )

    # Currently, we are creating one stream:
    #   Feed the data from IoT Core to S3 bucket while converting from JSON to Apache Parquet.
    def create_firehose_streams(self) -> aws_kinesisfirehose.CfnDeliveryStream:
        """
        Create Kinesis Firehose streams along with IAM role/policies.
        """
        # Create encrypted CloudWatch group/stream for Kinesis Firehose
        log_group_kms_key = aws_kms.Key(
            self,
            "iot-connectivity-log-group-key",
            enable_key_rotation=True,
        )

        log_group_kms_key.add_to_resource_policy(
            statement=aws_iam.PolicyStatement(
                effect=aws_iam.Effect.ALLOW,
                principals=[
                    aws_iam.ServicePrincipal(
                        f"logs.{Stack.of(self).region}.amazonaws.com"
                    )
                ],
                actions=[
                    "kms:Encrypt",
                    "kms:Decrypt",
                    "kms:GenerateDataKey",
                ],
                resources=["*"],
            )
        )

        log_group = aws_logs.LogGroup(
            self,
            "connect-store-iot-connectivity-logs",
            encryption_key=log_group_kms_key,
            retention=aws_logs.RetentionDays.THREE_MONTHS,
        )

        log_stream = aws_logs.LogStream(
            self,
            "connect-store-iot-connectivity-stream",
            log_group=log_group,
            log_stream_name="iot-connectivity-stream",
        )

        # This role will be used for kinesis stream to access glue and s3.
        kinesis_role = aws_iam.Role(
            self,
            "connect-store-kinesis-role",
            assumed_by=aws_iam.ServicePrincipal("firehose.amazonaws.com"),
            inline_policies={
                "kinesis-cloudwatch-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "logs:CreateLogGroup",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents",
                            ],
                            resources=[log_group.log_group_arn],
                        )
                    ],
                ),
                "glue-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "glue:GetTable",
                                "glue:GetTableVersion",
                                "glue:GetTableVersions",
                                "glue:GetDatabase",
                            ],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="glue",
                                    resource="database",
                                    resource_name=self.glue_database.database_input.name,  # type: ignore [union-attr]
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                                Stack.of(self).format_arn(
                                    service="glue",
                                    resource="table",
                                    resource_name=f"{self.glue_database.database_input.name}/{self.glue_table.table_input.name}",  # type: ignore [union-attr]
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                                Stack.of(self).format_arn(
                                    service="glue",
                                    resource="catalog",
                                    arn_format=ArnFormat.COLON_RESOURCE_NAME,
                                ),
                            ],
                        ),
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "glue:GetSchema",
                                "glue:GetSchemaVersion",
                                "glue:GetRegistry",
                            ],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="glue",
                                    resource="registry",
                                    resource_name=self.default_registry_name,
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                                self.glue_schema.attr_arn,
                            ],
                        ),
                    ],
                ),
                "s3-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "s3:AbortMultipartUpload",
                                "s3:GetBucketLocation",
                                "s3:GetObject",
                                "s3:ListBucket",
                                "s3:ListBucketMultipartUploads",
                                "s3:PutObject",
                            ],
                            resources=[
                                self.root_s3.bucket_arn,
                                self.root_s3.bucket_arn + "/*",
                            ],
                        ),
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "kms:Encrypt",
                                "kms:Decrypt",
                                "kms:GenerateDataKey",
                            ],
                            resources=[
                                self.root_s3.encryption_key.key_arn,  # type: ignore [union-attr]
                            ],
                        ),
                    ],
                ),
            },
            description="Service role for kinesis firehose",
        )

        kinesis_firehose_key = aws_kms.Key(
            self,
            "connect-store-kinesis-firehose-key",
            enable_key_rotation=True,
        )

        # Create delivery stream.
        cfn_main_stream = aws_kinesisfirehose.CfnDeliveryStream(
            self,
            "connect-store-iotcore-to-s3-with-partitioning-stream",
            delivery_stream_name="iotcore-to-s3-with-partitioning-stream",
            delivery_stream_type="DirectPut",
            delivery_stream_encryption_configuration_input=aws_kinesisfirehose.CfnDeliveryStream.DeliveryStreamEncryptionConfigurationInputProperty(
                key_type="CUSTOMER_MANAGED_CMK",
                key_arn=kinesis_firehose_key.key_arn,
            ),
            extended_s3_destination_configuration=aws_kinesisfirehose.CfnDeliveryStream.ExtendedS3DestinationConfigurationProperty(
                bucket_arn=self.root_s3.bucket_arn,
                role_arn=kinesis_role.role_arn,
                buffering_hints=aws_kinesisfirehose.CfnDeliveryStream.BufferingHintsProperty(
                    interval_in_seconds=60,
                    size_in_m_bs=128,
                ),
                cloud_watch_logging_options=aws_kinesisfirehose.CfnDeliveryStream.CloudWatchLoggingOptionsProperty(
                    enabled=True,
                    log_group_name=log_group.log_group_name,
                    log_stream_name=log_stream.log_stream_name,
                ),
                # Define data conversion from JSON to Apache Parquet.
                data_format_conversion_configuration=aws_kinesisfirehose.CfnDeliveryStream.DataFormatConversionConfigurationProperty(
                    enabled=True,
                    input_format_configuration=aws_kinesisfirehose.CfnDeliveryStream.InputFormatConfigurationProperty(
                        deserializer=aws_kinesisfirehose.CfnDeliveryStream.DeserializerProperty(
                            open_x_json_ser_de=aws_kinesisfirehose.CfnDeliveryStream.OpenXJsonSerDeProperty(
                                case_insensitive=False,
                                convert_dots_in_json_keys_to_underscores=False,
                            )
                        )
                    ),
                    output_format_configuration=aws_kinesisfirehose.CfnDeliveryStream.OutputFormatConfigurationProperty(
                        serializer=aws_kinesisfirehose.CfnDeliveryStream.SerializerProperty(
                            parquet_ser_de=aws_kinesisfirehose.CfnDeliveryStream.ParquetSerDeProperty(
                                enable_dictionary_compression=False,
                            ),
                        ),
                    ),
                    # Connect to AWS Glue table, which defines data format for the converter.
                    schema_configuration=aws_kinesisfirehose.CfnDeliveryStream.SchemaConfigurationProperty(
                        database_name=self.glue_database.database_input.name,  # type: ignore [union-attr]
                        region=Stack.of(self).region,
                        role_arn=kinesis_role.role_arn,
                        table_name=self.glue_table.table_input.name,  # type: ignore [union-attr]
                    ),
                ),
                # Define dynamic partitioning mechanism that creates targeted data sets
                # from the streaming data by partitioning it based on partition keys.
                # We are using it to create specific S3 prefixes.
                dynamic_partitioning_configuration=aws_kinesisfirehose.CfnDeliveryStream.DynamicPartitioningConfigurationProperty(
                    enabled=True,
                ),
                processing_configuration=aws_kinesisfirehose.CfnDeliveryStream.ProcessingConfigurationProperty(
                    enabled=True,
                    processors=[
                        aws_kinesisfirehose.CfnDeliveryStream.ProcessorProperty(
                            type="MetadataExtraction",
                            parameters=[
                                aws_kinesisfirehose.CfnDeliveryStream.ProcessorParameterProperty(
                                    parameter_name="MetadataExtractionQuery",
                                    parameter_value="{vin: .vehicleidentification.vin}",
                                ),
                                aws_kinesisfirehose.CfnDeliveryStream.ProcessorParameterProperty(
                                    parameter_name="JsonParsingEngine",
                                    parameter_value="JQ-1.6",
                                ),
                            ],
                        ),
                        aws_kinesisfirehose.CfnDeliveryStream.ProcessorProperty(
                            type="AppendDelimiterToRecord",
                            parameters=[
                                aws_kinesisfirehose.CfnDeliveryStream.ProcessorParameterProperty(
                                    parameter_name="Delimiter", parameter_value="\\n"
                                )
                            ],
                        ),
                    ],
                ),
                prefix="Parquet/!{partitionKeyFromQuery:vin}/!{timestamp:DDD}_!{timestamp:yyyy}/!{timestamp:HH}",
                error_output_prefix="DataError/",
            ),
        )
        cfn_main_stream.add_dependency(self.glue_database)
        cfn_main_stream.add_dependency(self.glue_table)

        return cfn_main_stream

    def setup_iot_core_rules(self) -> None:
        """
        Add iot_core rules.
        """

        # This role will be used for IoT Core to access S3 bucket.
        iotcore_to_s3_role = aws_iam.Role(
            self,
            "connect-store-iot-core-to-s3-role",
            assumed_by=aws_iam.ServicePrincipal("iot.amazonaws.com"),
            inline_policies={
                "s3-read-write-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "s3:GetBucket",
                                "s3:GetObject",
                                "s3:List",
                                "s3:PutObject",
                                "s3:DeleteObject",
                                "s3:Abort",
                            ],
                            resources=[
                                self.root_s3.bucket_arn,
                                self.root_s3.bucket_arn + "/*",
                            ],
                        ),
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "kms:Encrypt",
                                "kms:Decrypt",
                                "kms:GenerateDataKey",
                            ],
                            resources=[
                                self.root_s3.encryption_key.key_arn,  # type: ignore [union-attr]
                            ],
                        ),
                    ]
                ),
            },
        )

        iotcore_to_kinesis_role = aws_iam.Role(
            self,
            "connect-store-iot-core-to-kinesis-role",
            assumed_by=aws_iam.ServicePrincipal("iot.amazonaws.com"),
            inline_policies={
                "firehose-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=["firehose:PutRecord", "firehose:PutRecords"],
                            resources=[self.kinesis_firehouse_stream.attr_arn],
                        )
                    ]
                )
            },
        )

        # Create rule to save all data to S3 bucket in raw JSON.
        aws_iot.CfnTopicRule(
            self,
            "connect-store-iot-save-to-s3-json",
            rule_name="iot_save_to_s3_json",  # kebab case not allowed in iot-core rule name
            topic_rule_payload=aws_iot.CfnTopicRule.TopicRulePayloadProperty(
                sql=self.primary_iot_core_query,
                description="Save raw vss data in JSON format to S3 bucket.",
                actions=[
                    aws_iot.CfnTopicRule.ActionProperty(
                        s3=aws_iot.CfnTopicRule.S3ActionProperty(
                            bucket_name=self.root_s3.bucket_name,
                            key="${topic()}/${timestamp()}",
                            role_arn=iotcore_to_s3_role.role_arn,
                        ),
                    )
                ],
            ),
        )

        # Create rule to send data to kinesis firehose stream.
        aws_iot.CfnTopicRule(
            self,
            "connect-store-iot-send-to-kinesis",
            rule_name="iot_send_to_kinesis",  # kebab case not allowed in iot-core rule name
            topic_rule_payload=aws_iot.CfnTopicRule.TopicRulePayloadProperty(
                sql=self.primary_iot_core_query,
                description="Send payload to Kinesis Firehose stream for processing.",
                actions=[
                    aws_iot.CfnTopicRule.ActionProperty(
                        firehose=aws_iot.CfnTopicRule.FirehoseActionProperty(
                            role_arn=iotcore_to_kinesis_role.role_arn,
                            delivery_stream_name=self.kinesis_firehouse_stream.delivery_stream_name,  # type: ignore [arg-type]
                        ),
                    )
                ],
            ),
        )

        aws_iot.CfnTopicRule(
            self,
            "connect-store-iot-send-to-alarm-lambda",
            rule_name="iot_send_to_alarm_lambda",  # kebab case not allowed
            topic_rule_payload=aws_iot.CfnTopicRule.TopicRulePayloadProperty(
                sql=self.vehicle_notifications_iot_core_query,
                description="Send payload to vehicle_trigger_alarm lambda",
                actions=[
                    aws_iot.CfnTopicRule.ActionProperty(
                        lambda_=aws_iot.CfnTopicRule.LambdaActionProperty(
                            function_arn=self.alerts_construct.vehicle_trigger_alarm_lambda_function.function_arn
                        )
                    ),
                ],
            ),
        )
