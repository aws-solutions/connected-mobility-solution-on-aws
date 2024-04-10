# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
from attrs import define

# AWS Libraries
from aws_cdk import (
    ArnFormat,
    CfnMapping,
    CustomResource,
    Fn,
    Stack,
    aws_iam,
    aws_s3_assets,
)
from constructs import Construct

# CMS Common Library
from cms_common.config.stack_inputs import SolutionConfigInputs
from cms_common.constructs.custom_resource_lambda import CustomResourceLambdaConstruct

# Connected Mobility Solution on AWS
from ...handlers.custom_resource.function.main import CustomResourceTypes
from .module_integration import BackstageS3LocalAssetsConfigInputs


@define(auto_attribs=True, frozen=True)
class BackstageSourceAssetZipLocation:
    s3_bucket_name: str
    s3_object_key: str


class BackstageAssetsConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        solution_mapping: CfnMapping,
        solution_config_inputs: SolutionConfigInputs,
        local_asset_bucket_inputs: BackstageS3LocalAssetsConfigInputs,
        custom_resource_lambda_construct: CustomResourceLambdaConstruct,
    ) -> None:
        super().__init__(scope, construct_id)

        backstage_asset_custom_resource_policy = aws_iam.Policy(
            self,
            "s3-policy",
            statements=[
                aws_iam.PolicyStatement(
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "s3:GetBucketLocation",
                        "s3:GetObject",
                        "s3:ListBucket",
                        "s3:HeadObject",
                    ],
                    resources=[
                        Stack.of(self).format_arn(
                            service="s3",
                            resource=f'{solution_mapping.find_in_map("AssetsConfig", "S3AssetBucketBaseName")}-{Stack.of(self).region}',
                            resource_name=None,
                            account="",
                            region="",
                            arn_format=ArnFormat.NO_RESOURCE_NAME,
                        ),
                        Stack.of(self).format_arn(
                            service="s3",
                            resource=f'{solution_mapping.find_in_map("AssetsConfig", "S3AssetBucketBaseName")}-{Stack.of(self).region}',
                            resource_name="*",
                            account="",
                            region="",
                            arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                        ),
                    ],
                ),
                aws_iam.PolicyStatement(
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "s3:GetBucketLocation",
                        "s3:GetObject",
                        "s3:ListBucket",
                        "s3:PutObject",
                        "s3:HeadObject",
                    ],
                    resources=[
                        Stack.of(self).format_arn(
                            service="s3",
                            resource=local_asset_bucket_inputs.bucket_name,
                            resource_name=None,
                            account="",
                            region="",
                            arn_format=ArnFormat.NO_RESOURCE_NAME,
                        ),
                        Stack.of(self).format_arn(
                            service="s3",
                            resource=local_asset_bucket_inputs.bucket_name,
                            resource_name="*",
                            account="",
                            region="",
                            arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                        ),
                    ],
                ),
                aws_iam.PolicyStatement(
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "kms:GenerateDataKey",
                        "kms:Decrypt",
                        "kms:Encrypt",
                    ],
                    resources=[local_asset_bucket_inputs.bucket_key_arn],
                ),
            ],
        )

        custom_resource_lambda_construct.add_policy_to_custom_resource_lambda(
            backstage_asset_custom_resource_policy
        )

        exclude_list = [
            "dist",
            "dist-types",
            "build",
            "cdk.out",
            "__pycache__",
            ".pytest_cache",
            ".mypy_cache",
            ".cdk_cache",
            "None",
            "*_dependency_layer",
            ".vscode",
            "node_modules",
            "examples",
            ".venv",
            "staging",
            "global-s3-assets",
            "regional-s3-assets",
        ]

        backstage_zip = aws_s3_assets.Asset(
            self,
            "acdp-backstage-asset",
            path="./backstage",
            exclude=exclude_list,
        )

        backstage_zip_asset_key = Fn.join(
            "",
            [
                Fn.find_in_map(
                    "Solution",
                    "AssetsConfig",
                    "S3AssetKeyPrefix",
                ),
                f"/asset{backstage_zip.s3_object_key}",
            ],
        )
        backstage_zip_copy_custom_resource = CustomResource(
            self,
            "deployment-backstage-zip-asset",
            service_token=custom_resource_lambda_construct.function.function_arn,
            resource_type=f"Custom::{CustomResourceTypes.ResourceTypes.COPY_S3_OBJECT.value}",
            properties={
                "Resource": CustomResourceTypes.ResourceTypes.COPY_S3_OBJECT.value,
                "SourceBucket": f'{solution_mapping.find_in_map("AssetsConfig", "S3AssetBucketBaseName")}-{Stack.of(self).region}',
                "SourceKey": backstage_zip_asset_key,
                "DestinationBucket": local_asset_bucket_inputs.bucket_name,
                "DestinationKey": backstage_zip_asset_key,
            },
        )

        self.backstage_source_asset_zip_location = BackstageSourceAssetZipLocation(
            s3_bucket_name=backstage_zip_copy_custom_resource.get_att_string(
                "DestinationBucket"
            ),
            s3_object_key=backstage_zip_copy_custom_resource.get_att_string(
                "DestinationKey"
            ),
        )

        backstage_template_assets_source_key = f"{solution_config_inputs.solution_name}/{solution_config_inputs.solution_version}/backstage.zip"
        backstage_template_assets_destination_key = (
            local_asset_bucket_inputs.backstage_default_assets_prefix
        )

        CustomResource(
            self,
            "backstage-template-assets-copy-custom-resource",
            service_token=custom_resource_lambda_construct.function.function_arn,
            resource_type=f"Custom::{CustomResourceTypes.ResourceTypes.EXTRACT_S3_ZIP_TO_TARGET_BUCKET.value}",
            properties={
                "Resource": CustomResourceTypes.ResourceTypes.EXTRACT_S3_ZIP_TO_TARGET_BUCKET.value,
                "SourceBucket": f'{solution_mapping.find_in_map("AssetsConfig", "S3AssetBucketBaseName")}-{Stack.of(self).region}',
                "SourceZipKey": backstage_template_assets_source_key,
                "DestinationBucket": local_asset_bucket_inputs.bucket_name,
                "DestinationKeyPrefix": backstage_template_assets_destination_key,
            },
        )
