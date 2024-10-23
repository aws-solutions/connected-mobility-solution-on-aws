# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# AWS Libraries
from aws_cdk import (
    ArnFormat,
    Stack,
    aws_iam,
    aws_iot,
    aws_kinesisfirehose,
    aws_kms,
    aws_logs,
    aws_s3,
)
from constructs import Construct

# CMS Common Library
from cms_common.config.resource_names import ResourceName, ResourcePrefix
from cms_common.config.stack_inputs import SolutionConfigInputs
from cms_common.policy_generators.kms import generate_kms_policy_statement_from_key_id

# Connected Mobility Solution on AWS
from .cmk_encrypted_log_group import CMKEncryptedLogGroupConstruct
from .s3_to_glue import GlueResources


class IoTCoreToS3ParquetConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_unique_id: str,
        iot_core_query: str,
        root_s3_bucket: aws_s3.Bucket,
        glue_resources: GlueResources,
        solution_config_inputs: SolutionConfigInputs,
    ) -> None:
        super().__init__(scope, construct_id)

        cmk_encrypted_log_group = CMKEncryptedLogGroupConstruct(
            self,
            "iot-kinesis-log-group",
        )

        log_stream = aws_logs.LogStream(
            self,
            "iot-kinesis-log-stream",
            log_group=cmk_encrypted_log_group.log_group,
            log_stream_name=ResourceName.hyphen_separated(
                prefix=ResourcePrefix.hyphen_separated(
                    app_unique_id=app_unique_id,
                    module_name=solution_config_inputs.module_short_name,
                ),
                name="iot-connectivity-stream",
            ),
        )

        # This role will be used for kinesis stream to access glue and s3.
        kinesis_role = aws_iam.Role(
            self,
            "kinesis-role",
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
                            resources=[cmk_encrypted_log_group.log_group.log_group_arn],
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
                                    resource_name=glue_resources.glue_database.database_input.name,  # type: ignore [union-attr]
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                                Stack.of(self).format_arn(
                                    service="glue",
                                    resource="table",
                                    resource_name=f"{glue_resources.glue_database.database_input.name}/{glue_resources.glue_table.table_input.name}",  # type: ignore [union-attr]
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
                                    resource_name=glue_resources.glue_schema.registry.name,  # type: ignore [union-attr]
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                                glue_resources.glue_schema.attr_arn,
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
                                root_s3_bucket.bucket_arn,
                                root_s3_bucket.bucket_arn + "/*",
                            ],
                        ),
                        generate_kms_policy_statement_from_key_id(
                            self,
                            kms_encryption_key_id=root_s3_bucket.encryption_key.key_id,  # type: ignore[union-attr]
                            allow_encrypt=True,
                        ),
                    ],
                ),
            },
            description="Service role for kinesis firehose",
        )

        kinesis_firehose_key = aws_kms.Key(
            self,
            "kinesis-firehose-key",
            enable_key_rotation=True,
        )

        # Create delivery stream.
        cfn_main_stream = aws_kinesisfirehose.CfnDeliveryStream(
            self,
            "iotcore-to-s3-with-partitioning-stream",
            delivery_stream_name=ResourceName.hyphen_separated(
                prefix=ResourcePrefix.hyphen_separated(
                    app_unique_id=app_unique_id,
                    module_name=solution_config_inputs.module_short_name,
                ),
                name="iot-to-s3-with-partitioning",
            ),
            delivery_stream_type="DirectPut",
            delivery_stream_encryption_configuration_input=aws_kinesisfirehose.CfnDeliveryStream.DeliveryStreamEncryptionConfigurationInputProperty(
                key_type="CUSTOMER_MANAGED_CMK",
                key_arn=kinesis_firehose_key.key_arn,
            ),
            extended_s3_destination_configuration=aws_kinesisfirehose.CfnDeliveryStream.ExtendedS3DestinationConfigurationProperty(
                bucket_arn=root_s3_bucket.bucket_arn,
                role_arn=kinesis_role.role_arn,
                buffering_hints=aws_kinesisfirehose.CfnDeliveryStream.BufferingHintsProperty(
                    interval_in_seconds=60,
                    size_in_m_bs=128,
                ),
                cloud_watch_logging_options=aws_kinesisfirehose.CfnDeliveryStream.CloudWatchLoggingOptionsProperty(
                    enabled=True,
                    log_group_name=cmk_encrypted_log_group.log_group.log_group_name,
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
                        database_name=glue_resources.glue_database.database_input.name,  # type: ignore [union-attr]
                        region=Stack.of(self).region,
                        role_arn=kinesis_role.role_arn,
                        table_name=glue_resources.glue_table.table_input.name,  # type: ignore [union-attr]
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

        iotcore_to_kinesis_role = aws_iam.Role(
            self,
            "iot-core-to-kinesis-role",
            assumed_by=aws_iam.ServicePrincipal("iot.amazonaws.com"),
            inline_policies={
                "firehose-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=["firehose:PutRecord", "firehose:PutRecords"],
                            resources=[cfn_main_stream.attr_arn],
                        )
                    ]
                )
            },
        )

        # Create rule to send data to kinesis firehose stream.
        aws_iot.CfnTopicRule(
            self,
            "iot-send-to-kinesis",
            rule_name=ResourceName.underscore_separated(
                prefix=ResourcePrefix.only_underscore_separated(
                    app_unique_id=app_unique_id,
                    module_name=solution_config_inputs.module_short_name,
                ),
                name="iot_send_to_kinesis",
            ),
            topic_rule_payload=aws_iot.CfnTopicRule.TopicRulePayloadProperty(
                sql=iot_core_query,
                description="Send payload to Kinesis Firehose stream for processing.",
                actions=[
                    aws_iot.CfnTopicRule.ActionProperty(
                        firehose=aws_iot.CfnTopicRule.FirehoseActionProperty(
                            role_arn=iotcore_to_kinesis_role.role_arn,
                            delivery_stream_name=cfn_main_stream.delivery_stream_name,  # type: ignore [arg-type]
                        ),
                    )
                ],
            ),
        )
