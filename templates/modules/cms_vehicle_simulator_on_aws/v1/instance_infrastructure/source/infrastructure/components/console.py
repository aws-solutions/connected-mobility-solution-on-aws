# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

# Standard Library
import json
import os
from typing import TYPE_CHECKING, Any

# Third Party Libraries
from aws_cdk import (
    ArnFormat,
    Aws,
    CustomResource,
    Fn,
    Stack,
    aws_cognito,
    aws_iam,
    aws_iot,
    aws_location,
    aws_s3,
    aws_s3_deployment,
    aws_ssm,
)
from constructs import Construct

# Connected Mobility Solution on AWS
from ...config.constants import VSConstants

if TYPE_CHECKING:
    # Connected Mobility Solution on AWS
    from ..cms_vehicle_simulator_on_aws_stack import InfrastructureConsoleStack


class ConsoleConstruct(Construct):
    def __init__(
        self,
        scope: InfrastructureConsoleStack,
        stack_id: str,
        api_id: str,
        api_endpoint: str,
        template_folder_path: str,
    ) -> None:
        super().__init__(scope, stack_id)

        self.ids_map = aws_location.CfnMap(
            self,
            "iot-device-simulator-map",
            configuration={"style": "VectorEsriNavigation"},
            map_name=f"{Fn.import_value(f'{VSConstants.APP_NAME}-reduced-stack-name')}-IotDeviceSimulatorMap-{Fn.import_value(f'{VSConstants.APP_NAME}-unique-suffix')}",
            pricing_plan="RequestBasedUsage",
        )

        self.ids_place_index = aws_location.CfnPlaceIndex(
            self,
            "iot-device-simulator-place-index",
            data_source="Esri",
            index_name=f"{Fn.import_value(f'{VSConstants.APP_NAME}-reduced-stack-name')}-IoTDeviceSimulatorPlaceIndex-{Fn.import_value(f'{VSConstants.APP_NAME}-unique-suffix')}",
            pricing_plan="RequestBasedUsage",
        )

        authenticated_role = aws_iam.Role(
            self,
            "identity-pool-authenticated-role",
            assumed_by=aws_iam.FederatedPrincipal(
                "cognito-identity.amazonaws.com",
                conditions={
                    "StringEquals": {
                        "cognito-identity.amazonaws.com:aud": Fn.import_value(
                            f"{VSConstants.APP_NAME}-identity-pool-ref"
                        )
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
                                    resource_name=f"{VSConstants.TOPIC_PREFIX}/*",
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
                                    resource_name=f"{VSConstants.TOPIC_PREFIX}/*",
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
            identity_pool_id=Fn.import_value(
                f"{VSConstants.APP_NAME}-identity-pool-ref"
            ),
            roles={"authenticated": authenticated_role.role_arn},
        )

        self.setup_ui(
            api_endpoint=api_endpoint, template_folder_path=template_folder_path
        )
        self.detach_iot_policy()

    def setup_ui(
        self,
        api_endpoint: str,
        template_folder_path: str,
    ) -> None:
        source_code_bucket = aws_s3.Bucket.from_bucket_arn(
            self,
            "source-code-bucket",
            Fn.import_value(f"{VSConstants.APP_NAME}-console-bucket-arn"),
        )

        aws_s3_deployment.BucketDeployment(
            self,
            "console-bucket-deployment",
            sources=[aws_s3_deployment.Source.asset("./source/console/build")],
            exclude=["aws_config.js"],
            destination_bucket=source_code_bucket,
            prune=False,
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
                                resource_name=f"{VSConstants.TOPIC_PREFIX}/*",
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
                                resource_name=f"{VSConstants.TOPIC_PREFIX}/*",
                                arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                            )
                        ],
                    ),
                ]
            ),
        )

        config = {
            "aws_iot_endpoint": Fn.import_value(
                f"{VSConstants.APP_NAME}-iot-end-point"
            ),
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
                "identityPoolId": Fn.import_value(
                    f"{VSConstants.APP_NAME}-identity-pool-ref"
                ),
                "region": Stack.of(self).region,
                "userPoolId": Fn.import_value(f"{VSConstants.APP_NAME}-user-pool-id"),
                "userPoolWebClientId": Fn.import_value(
                    f"{VSConstants.APP_NAME}-user-pool-client-id"
                ),
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
            "topic_prefix": VSConstants.TOPIC_PREFIX,
        }

        self.upload_console_config(config)
        templates = os.listdir(template_folder_path)
        for template_name in templates:
            if template_name.endswith(".json"):
                template_path = os.path.join(template_folder_path, template_name)
                with open(template_path, "r", encoding="utf-8") as vss_file:
                    template_json_string = vss_file.read()
                    template_json = json.loads(template_json_string)

                self.upload_json_template(template_json, template_name)

    def upload_console_config(self, console_config: Any) -> None:
        CustomResource(
            self,
            "console-config",
            service_token=Fn.import_value(
                f"{VSConstants.APP_NAME}-helper-function-arn"
            ),
            resource_type="Custom::CopyConfigFiles",
            properties={
                "Resource": "CreateConfig",
                "ConfigFileName": "aws_config.js",
                "DestinationBucket": Fn.import_value(
                    f"{VSConstants.APP_NAME}-console-bucket-name"
                ),
                "configObj": json.dumps(console_config, separators=(",", ":")),
            },
        )

    def detach_iot_policy(self) -> None:
        CustomResource(
            self,
            "detach-iot-policy",
            service_token=Fn.import_value(
                f"{VSConstants.APP_NAME}-helper-function-arn"
            ),
            properties={
                "Resource": "DetachIoTPolicy",
                "IoTPolicyName": self.iot_policy.ref,
            },
        )

    def upload_json_template(
        self, vss_json: dict[str, Any], template_name: str
    ) -> None:
        CustomResource(
            self,
            f"custom-template-{template_name}",
            resource_type="Custom::CopyTemplate",
            service_token=Fn.import_value(
                f"{VSConstants.APP_NAME}-helper-function-arn"
            ),
            properties={
                "TableName": aws_ssm.StringParameter.from_string_parameter_name(
                    self,
                    "ssm-templates-table-name",
                    f"/{VSConstants.STAGE}/{VSConstants.APP_NAME}/dynamodb/templates-table-name",
                ).string_value,
                "Resource": "CopyTemplate",
                "Template": json.dumps(vss_json, separators=(",", ":")),
            },
        )
