# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
from attrs import define

# AWS Libraries
from aws_cdk import CfnParameter, RemovalPolicy, Stack, aws_s3
from constructs import Construct


@define(auto_attribs=True, frozen=True)
class LifecycleConfig:
    expiration_days: int | float = 90
    noncurrent_version_expiration_days: int | float = 1
    abort_incomplete_multipart_upload_after_days: int | float = 1


class EncryptedS3Construct(Construct):
    @staticmethod
    def create_log_lifecycle_cfn_parameters(
        scope: Construct,
    ) -> LifecycleConfig:
        log_bucket_expiration_days_param = CfnParameter(
            Stack.of(scope),
            "S3LogExpirationDays",
            type="Number",
            default=90,
            description="The number of days before log bucket objects expire.",
        )
        log_bucket_noncurrent_expiration_param = CfnParameter(
            Stack.of(scope),
            "S3LogNoncurrentVersionExpirationDays",
            type="Number",
            default=1,
            description="The number of days before log bucket non-current versions are deleted after they've expired.",
        )

        return LifecycleConfig(
            expiration_days=log_bucket_expiration_days_param.value_as_number,
            noncurrent_version_expiration_days=log_bucket_noncurrent_expiration_param.value_as_number,
        )

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        retain_on_stack_delete: bool = True,
        log_lifecycle_rules: LifecycleConfig = LifecycleConfig()
    ) -> None:
        super().__init__(scope, construct_id)

        self.log_bucket = EncryptedS3Construct.create_log_bucket(
            self, "log-bucket", log_lifecycle_rules=log_lifecycle_rules
        )

        # Create the main bucket with server access logs pointing to the log bucket.
        self.bucket = aws_s3.Bucket(
            self,
            "encrypted-bucket",
            enforce_ssl=True,
            encryption=aws_s3.BucketEncryption.S3_MANAGED,
            server_access_logs_bucket=self.log_bucket,
            block_public_access=aws_s3.BlockPublicAccess.BLOCK_ALL,
            versioned=True,
            auto_delete_objects=(not retain_on_stack_delete),
            removal_policy=(
                RemovalPolicy.RETAIN
                if retain_on_stack_delete
                else RemovalPolicy.DESTROY
            ),
        )

    @staticmethod
    def create_log_bucket(
        scope: Construct,
        bucket_id: str,
        log_lifecycle_rules: LifecycleConfig = LifecycleConfig(),
    ) -> aws_s3.IBucket:

        log_bucket = aws_s3.Bucket(
            scope,
            bucket_id,
            enforce_ssl=True,
            block_public_access=aws_s3.BlockPublicAccess.BLOCK_ALL,
            versioned=True,
            encryption=aws_s3.BucketEncryption.S3_MANAGED,
        )

        EncryptedS3Construct.add_lifecycle_to_bucket(
            s3_bucket=log_bucket,
            lifecycle_rules=log_lifecycle_rules,
        )

        return log_bucket

    @staticmethod
    def add_lifecycle_to_bucket(
        s3_bucket: aws_s3.IBucket, lifecycle_rules: LifecycleConfig = LifecycleConfig()
    ) -> None:

        # need to use cfn_bucket to be able to pass cfn param values
        # since cdk properties use Duration which doesn't support dynamic values
        cfn_bucket = s3_bucket.node.default_child
        cfn_bucket.add_property_override(  # type: ignore[union-attr]
            "LifecycleConfiguration",
            {
                "Rules": [
                    {
                        "Id": "expire-current-version-and-delete-old-objects",
                        "Status": "Enabled",
                        "ExpirationInDays": lifecycle_rules.expiration_days,
                        "NoncurrentVersionExpirationInDays": lifecycle_rules.noncurrent_version_expiration_days,
                        "AbortIncompleteMultipartUpload": {
                            "DaysAfterInitiation": lifecycle_rules.abort_incomplete_multipart_upload_after_days
                        },
                    }
                ]
            },
        )
