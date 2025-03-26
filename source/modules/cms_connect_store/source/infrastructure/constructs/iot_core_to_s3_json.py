# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# AWS Libraries
from aws_cdk import aws_iam, aws_iot, aws_s3
from constructs import Construct

# CMS Common Library
from cms_common.config.resource_names import ResourceName, ResourcePrefix
from cms_common.config.stack_inputs import SolutionConfigInputs


class IoTCoreToS3JsonConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_unique_id: str,
        iot_core_query: str,
        root_s3_bucket: aws_s3.Bucket,
        solution_config_inputs: SolutionConfigInputs,
    ) -> None:
        super().__init__(scope, construct_id)

        # This role will be used for IoT Core to access S3 bucket.
        iotcore_to_s3_role = aws_iam.Role(
            self,
            "iot-core-to-s3-role",
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
                                root_s3_bucket.bucket_arn,
                                root_s3_bucket.bucket_arn + "/*",
                            ],
                        ),
                    ]
                ),
            },
        )

        # Create rule to save all data to S3 bucket in raw JSON.
        aws_iot.CfnTopicRule(
            self,
            "iot-save-to-s3-json",
            rule_name=ResourceName.underscore_separated(
                prefix=ResourcePrefix.only_underscore_separated(
                    app_unique_id=app_unique_id,
                    module_name=solution_config_inputs.module_short_name,
                ),
                name="iot_save_to_s3_json",
            ),
            topic_rule_payload=aws_iot.CfnTopicRule.TopicRulePayloadProperty(
                sql=iot_core_query,
                description="Save raw vss data in JSON format to S3 bucket.",
                actions=[
                    aws_iot.CfnTopicRule.ActionProperty(
                        s3=aws_iot.CfnTopicRule.S3ActionProperty(
                            bucket_name=root_s3_bucket.bucket_name,
                            key="${topic()}/${timestamp()}",
                            role_arn=iotcore_to_s3_role.role_arn,
                        ),
                    )
                ],
            ),
        )
