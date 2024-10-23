# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# AWS Libraries
from aws_cdk import RemovalPolicy, aws_kms, aws_s3
from constructs import Construct


class CMKEncryptedS3Construct(Construct):
    def __init__(
        self, scope: Construct, construct_id: str, retain_on_stack_delete: bool = True
    ) -> None:
        super().__init__(scope, construct_id)

        self.key = aws_kms.Key(
            self,
            "cmk-key",
            enable_key_rotation=True,
        )

        self.log_bucket = aws_s3.Bucket(
            self,
            "log-bucket",
            enforce_ssl=True,
            block_public_access=aws_s3.BlockPublicAccess.BLOCK_ALL,
            versioned=True,
            encryption=aws_s3.BucketEncryption.KMS,
            encryption_key=self.key,
        )

        self.bucket: aws_s3.Bucket = aws_s3.Bucket(
            self,
            "cmk-encrypted-bucket",
            enforce_ssl=True,
            encryption_key=self.key,
            encryption=aws_s3.BucketEncryption.KMS,
            server_access_logs_bucket=self.log_bucket,
            block_public_access=aws_s3.BlockPublicAccess.BLOCK_ALL,
            versioned=True,
            auto_delete_objects=(not retain_on_stack_delete),
            removal_policy=RemovalPolicy.RETAIN
            if retain_on_stack_delete
            else RemovalPolicy.DESTROY,
        )
