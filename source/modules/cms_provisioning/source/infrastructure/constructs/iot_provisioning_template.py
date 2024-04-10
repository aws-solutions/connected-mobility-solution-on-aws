# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json

# AWS Libraries
from aws_cdk import ArnFormat, Stack, aws_iam, aws_iot
from constructs import Construct


class IoTProvisioningTemplateConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        provisioning_template_txt: str,
        pre_provisioning_lambda_arn: str,
        provisioning_template_name: str,
    ) -> None:
        super().__init__(scope, construct_id)

        # This role will be used by IoT Core to provision new vehicles.
        iotcore_provisioning_role = aws_iam.Role(
            self,
            "iot-core-provisioning-role",
            assumed_by=aws_iam.ServicePrincipal("iot.amazonaws.com"),
            inline_policies={
                "provisioning-template-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "iot:RegisterThing",
                                "iot:CreatePolicy",
                            ],
                            resources=[
                                "*"  # NOSONAR
                            ],  # These actions require a wildcard resource
                        ),
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "iot:AttachPrincipalPolicy",
                                "iot:AttachThingPrincipal",
                                "iot:DescribeCertificate",
                                "iot:UpdateCertificate",
                            ],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="iot",
                                    resource="cert",
                                    resource_name="*",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                            ],
                        ),
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "iot:CreateThing",
                                "iot:DescribeThing",
                                "iot:ListThingGroupsForThing",
                                "iot:UpdateThing",
                            ],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="iot",
                                    resource="thing",
                                    resource_name="*",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                            ],
                        ),
                    ],
                ),
            },
        )

        # Substitute variables defined
        template_txt = provisioning_template_txt
        template_txt = template_txt.replace("$aws_region", Stack.of(self).region)
        template_txt = template_txt.replace("$aws_account", Stack.of(self).account)
        template_txt = template_txt.replace(
            "$provisioning_template_name", provisioning_template_name
        )

        # Convert and validate that the string is a valid JSON string
        provisioning_template_json = json.loads(template_txt)

        # Create template resource which will be used for provisioning new vehicles.
        aws_iot.CfnProvisioningTemplate(
            self,
            "fleet-provisioning-template",
            provisioning_role_arn=iotcore_provisioning_role.role_arn,
            template_body=json.dumps(provisioning_template_json),
            description="Template used to provision new vehicle",
            enabled=True,
            pre_provisioning_hook=aws_iot.CfnProvisioningTemplate.ProvisioningHookProperty(
                target_arn=pre_provisioning_lambda_arn,
            ),
            template_name=provisioning_template_name,
        )
