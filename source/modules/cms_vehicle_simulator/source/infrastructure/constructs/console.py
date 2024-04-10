# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

# Standard Library
import json
import os
from typing import Any

# AWS Libraries
from aws_cdk import (
    ArnFormat,
    Aws,
    CustomResource,
    Stack,
    aws_cognito,
    aws_iam,
    aws_iot,
    aws_location,
    aws_s3,
    aws_s3_deployment,
)
from constructs import Construct

# CMS Common Library
from cms_common.constructs.custom_resource_lambda import CustomResourceLambdaConstruct
from cms_common.constructs.vpc_construct import VpcConstruct

# Connected Mobility Solution on AWS
from .cloudfront import CloudFrontConstruct
from .cognito import CognitoConstruct
from .storage import StorageConstruct


class ConsoleConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        stack_id: str,
        api_id: str,
        api_endpoint: str,
        template_folder_path: str,
        storage_construct: StorageConstruct,
        custom_resource_lambda_construct: CustomResourceLambdaConstruct,
        cognito_construct: CognitoConstruct,
        cloudfront_construct: CloudFrontConstruct,
        iot_endpoint: str,
        iot_topic_prefix: str,
        vpc_construct: VpcConstruct,
    ) -> None:
        super().__init__(scope, stack_id)

        self.identity_pool_ref = cognito_construct.identity_pool.ref
        self.user_pool_id = cognito_construct.user_pool.user_pool_id
        self.user_pool_client_id = (
            cognito_construct.user_pool_client.user_pool_client_id
        )
        self.custom_resources_lambda_function_arn = (
            custom_resource_lambda_construct.function.function_arn
        )
        self.console_bucket_arn = (
            cloudfront_construct.console_cloudfront_dist.s3_bucket.bucket_arn  # type: ignore[union-attr]
        )
        self.console_bucket_name = (
            cloudfront_construct.console_cloudfront_dist.s3_bucket.bucket_name  # type: ignore[union-attr]
        )
        self.iot_endpoint = iot_endpoint
        self.iot_topic_prefix = iot_topic_prefix

        self.console_custom_resource_policy = aws_iam.Policy(
            self,
            "custom-resource-policy",
            statements=[
                aws_iam.PolicyStatement(
                    effect=aws_iam.Effect.ALLOW,
                    actions=["dynamodb:PutItem"],
                    resources=[
                        storage_construct.templates_table.table_arn,
                    ],
                ),
                aws_iam.PolicyStatement(
                    effect=aws_iam.Effect.ALLOW,
                    actions=["s3:PutObject", "s3:AbortMultipartUpload"],
                    resources=[
                        f"{cloudfront_construct.console_cloudfront_dist.s3_bucket.bucket_arn}/*",  # type: ignore[union-attr]
                        f"{cloudfront_construct.routes_bucket.bucket_arn}/*",
                    ],
                ),
                aws_iam.PolicyStatement(
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "iot:DescribeEndpoint",
                        "iot:TagResource",
                        "iot:DetachPrincipalPolicy",
                    ],
                    resources=["*"],  # NOSONAR
                    # These actions require a wildcard resource
                ),
                aws_iam.PolicyStatement(
                    actions=["iot:ListTargetsForPolicy"],
                    effect=aws_iam.Effect.ALLOW,
                    resources=[
                        Stack.of(self).format_arn(
                            service="iot",
                            resource="policy",
                            resource_name="*",
                            arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                        )
                    ],
                ),
            ],
        )
        custom_resource_lambda_construct.add_policy_to_custom_resource_lambda(
            policy=self.console_custom_resource_policy
        )

        custom_ids_custom_resource = CustomResource(
            self,
            "console-uuid-custom-resource",
            service_token=custom_resource_lambda_construct.function.function_arn,
            properties={"Resource": "CreateUUID", "StackName": Aws.STACK_NAME},
        )
        custom_ids_custom_resource.node.add_dependency(
            self.console_custom_resource_policy
        )

        self.ids_map = aws_location.CfnMap(
            self,
            "iot-device-simulator-map",
            configuration={"style": "VectorEsriNavigation"},
            map_name=custom_ids_custom_resource.get_att(
                "REDUCED_STACK_NAME"
            ).to_string()
            + "-IoTDeviceSimulatorPlaceIndex-"
            + custom_ids_custom_resource.get_att("UNIQUE_SUFFIX").to_string(),
            pricing_plan="RequestBasedUsage",
        )

        self.ids_place_index = aws_location.CfnPlaceIndex(
            self,
            "iot-device-simulator-place-index",
            data_source="Esri",
            index_name=custom_ids_custom_resource.get_att(
                "REDUCED_STACK_NAME"
            ).to_string()
            + "-IoTDeviceSimulatorPlaceIndex-"
            + custom_ids_custom_resource.get_att("UNIQUE_SUFFIX").to_string(),
            pricing_plan="RequestBasedUsage",
        )

        authenticated_role = aws_iam.Role(
            self,
            "identity-pool-authenticated-role",
            assumed_by=aws_iam.FederatedPrincipal(
                "cognito-identity.amazonaws.com",
                conditions={
                    "StringEquals": {
                        "cognito-identity.amazonaws.com:aud": cognito_construct.identity_pool.ref,
                    },
                    "ForAnyValue:StringLike": {
                        "cognito-identity.amazonaws.com:amr": "authenticated"
                    },
                },
                assume_role_action="sts:AssumeRoleWithWebIdentity",
            ),
            description=f"{Aws.STACK_NAME} Identity Pool authenticated role",
            inline_policies={
                "execute-api-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=["execute-api:Invoke"],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="execute-api",
                                    resource=f"{api_id}",
                                    resource_name="*",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                )
                            ],
                        )
                    ]
                ),
                "location-service-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "geo:SearchPlaceIndexForText",
                                "geo:GetMapGlyphs",
                                "geo:GetMapSprites",
                                "geo:GetMapStyleDescriptor",
                                "geo:SearchPlaceIndexForPosition",
                                "execute-api:Invoke",
                                "geo:GetMapTile",
                            ],
                            resources=[
                                self.ids_map.attr_map_arn,
                                self.ids_place_index.attr_index_arn,
                            ],
                        )
                    ]
                ),
                "iot-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=["iot:AttachPolicy"],
                            resources=["*"],  # NOSONAR
                            # These actions require a wildcard resource
                        ),
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=["iot:Connect"],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="iot",
                                    resource="client",
                                    resource_name="*",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                )
                            ],
                        ),
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=["iot:Subscribe"],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="iot",
                                    resource="topicfilter",
                                    resource_name=f"{self.iot_topic_prefix}/*",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                )
                            ],
                        ),
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=["iot:Receive"],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="iot",
                                    resource="topic",
                                    resource_name=f"{self.iot_topic_prefix}/*",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                )
                            ],
                        ),
                    ]
                ),
            },
        )

        aws_cognito.CfnIdentityPoolRoleAttachment(
            self,
            "identity-pool-role-attachment",
            identity_pool_id=cognito_construct.identity_pool.ref,
            roles={"authenticated": authenticated_role.role_arn},
        )

        self.setup_ui(
            api_endpoint=api_endpoint,
            template_folder_path=template_folder_path,
            template_table_name=storage_construct.templates_table.table_name,
            vpc_construct=vpc_construct,
        )
        self.detach_iot_policy()

    def setup_ui(
        self,
        api_endpoint: str,
        template_folder_path: str,
        template_table_name: str,
        vpc_construct: VpcConstruct,
    ) -> None:
        source_code_bucket = aws_s3.Bucket.from_bucket_arn(
            self,
            "source-code-bucket",
            self.console_bucket_arn,
        )

        aws_s3_deployment.BucketDeployment(
            self,
            "console-bucket-deployment",
            sources=[aws_s3_deployment.Source.asset("./source/console/build")],
            exclude=["aws_config.js"],
            destination_bucket=source_code_bucket,
            prune=False,
            vpc=vpc_construct.vpc,
            vpc_subnets=vpc_construct.private_subnet_selection,
        )

        self.iot_policy = aws_iot.CfnPolicy(
            self,
            "vs-iot-policy",
            policy_document=aws_iam.PolicyDocument(
                statements=[
                    aws_iam.PolicyStatement(
                        effect=aws_iam.Effect.ALLOW,
                        actions=["iot:Connect"],
                        resources=[
                            Stack.of(self).format_arn(
                                service="iot",
                                resource="client",
                                resource_name="*",
                                arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                            )
                        ],
                    ),
                    aws_iam.PolicyStatement(
                        effect=aws_iam.Effect.ALLOW,
                        actions=["iot:Subscribe"],
                        resources=[
                            Stack.of(self).format_arn(
                                service="iot",
                                resource="topicfilter",
                                resource_name=f"{self.iot_topic_prefix}/*",
                                arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                            )
                        ],
                    ),
                    aws_iam.PolicyStatement(
                        effect=aws_iam.Effect.ALLOW,
                        actions=["iot:Receive"],
                        resources=[
                            Stack.of(self).format_arn(
                                service="iot",
                                resource="topic",
                                resource_name=f"{self.iot_topic_prefix}/*",
                                arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                            )
                        ],
                    ),
                ]
            ),
        )

        config = {
            "aws_iot_endpoint": self.iot_endpoint,
            "API": {
                "endpoints": [
                    {
                        "name": "ids",
                        "endpoint": api_endpoint,
                        "region": Stack.of(self).region,
                    }
                ]
            },
            "Auth": {
                "identityPoolId": self.identity_pool_ref,
                "region": Stack.of(self).region,
                "userPoolId": self.user_pool_id,
                "userPoolWebClientId": self.user_pool_client_id,
            },
            "aws_iot_policy_name": self.iot_policy.ref,
            "aws_project_region": Stack.of(self).region,
            "geo": {
                "AmazonLocationService": {
                    "region": Stack.of(self).region,
                    "maps": {
                        "items": {
                            self.ids_map.map_name: {
                                "style": "VectorEsriNavigation",
                            },
                        },
                        "default": self.ids_map.map_name,
                    },
                    "search_indices": {
                        "items": [self.ids_place_index.index_name],
                        "default": self.ids_place_index.index_name,
                    },
                }
            },
            "topic_prefix": self.iot_topic_prefix,
        }

        self.upload_console_config(config)
        templates = os.listdir(template_folder_path)
        for template_name in templates:
            if template_name.endswith(".json"):
                template_path = os.path.join(template_folder_path, template_name)
                with open(template_path, "r", encoding="utf-8") as vss_file:
                    template_json_string = vss_file.read()
                    template_json = json.loads(template_json_string)

                self.upload_json_template(
                    vss_json=template_json,
                    template_name=template_name,
                    template_table_name=template_table_name,
                )

    def upload_console_config(self, console_config: Any) -> None:
        console_config_custom_resource = CustomResource(
            self,
            "console-config",
            service_token=self.custom_resources_lambda_function_arn,
            resource_type="Custom::CopyConfigFiles",
            properties={
                "Resource": "CreateConfig",
                "ConfigFileName": "aws_config.js",
                "DestinationBucket": self.console_bucket_name,
                "configObj": json.dumps(console_config, separators=(",", ":")),
            },
        )
        console_config_custom_resource.node.add_dependency(
            self.console_custom_resource_policy
        )

    def detach_iot_policy(self) -> None:
        detach_iot_policy_custom_resource = CustomResource(
            self,
            "detach-iot-policy",
            service_token=self.custom_resources_lambda_function_arn,
            properties={
                "Resource": "DetachIoTPolicy",
                "IoTPolicyName": self.iot_policy.ref,
            },
        )
        detach_iot_policy_custom_resource.node.add_dependency(
            self.console_custom_resource_policy
        )

    def upload_json_template(
        self,
        vss_json: dict[str, Any],
        template_name: str,
        template_table_name: str,
    ) -> None:
        upload_json_template_custom_resource = CustomResource(
            self,
            f"custom-template-{template_name}",
            resource_type="Custom::CopyTemplate",
            service_token=self.custom_resources_lambda_function_arn,
            properties={
                "TableName": template_table_name,
                "Resource": "CopyTemplate",
                "Template": json.dumps(vss_json, separators=(",", ":")),
            },
        )
        upload_json_template_custom_resource.node.add_dependency(
            self.console_custom_resource_policy
        )
