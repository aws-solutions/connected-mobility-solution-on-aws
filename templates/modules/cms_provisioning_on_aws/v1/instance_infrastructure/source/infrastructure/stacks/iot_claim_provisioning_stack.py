# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json
from typing import Any

# Third Party Libraries
from aws_cdk import (
    ArnFormat,
    CfnOutput,
    CustomResource,
    NestedStack,
    Stack,
    aws_iam,
    aws_iot,
    aws_ssm,
)
from constructs import Construct

# Connected Mobility Solution on AWS
from ...config.constants import VPConstants
from ...handlers.custom_resource.lib.custom_resource_type_enum import CustomResourceType


# Setup IoT Core for JIT Fleet Provisioning by claim.
# https://docs.aws.amazon.com/iot/latest/developerguide/provision-wo-cert.html
class IoTClaimProvisioningStack(NestedStack):
    def __init__(
        self,
        scope: Construct,
        stack_id: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, stack_id, **kwargs)

        self.setup_iot_core_provisioning_template()
        self.setup_iot_core_claim_certificate()

    def setup_iot_core_provisioning_template(self) -> None:
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

        with open("template.json", encoding="utf-8") as file:
            template_text = file.read()

        # Substitute variables defined
        template_text = template_text.replace("$aws_region", f"{self.region}")
        template_text = template_text.replace("$aws_account", f"{self.account}")

        # Convert and validate
        template_json = json.loads(template_text)

        # Create template resource which will be used for provisioning new vehicles.
        aws_iot.CfnProvisioningTemplate(
            self,
            "fleet-provisioning-template",
            provisioning_role_arn=iotcore_provisioning_role.role_arn,
            template_body=json.dumps(template_json),
            description="Template used to provision new vehicle",
            enabled=True,
            pre_provisioning_hook=aws_iot.CfnProvisioningTemplate.ProvisioningHookProperty(
                target_arn=aws_ssm.StringParameter.from_string_parameter_name(
                    self,
                    "pre-provisioning-lambda-arn-value",
                    f"/{VPConstants.STAGE}/{VPConstants.APP_NAME}/arns/pre-provisioning-lambda-arn",
                ).string_value,
            ),
            template_name=VPConstants.PROVISIONING_TEMPLATE_NAME,
        )

    def setup_iot_core_claim_certificate(self) -> None:
        provisioning_secret_id = (
            f"{VPConstants.STAGE}/{VPConstants.APP_NAME}/provisioning-credentials"
        )
        self.iot_credentials = CustomResource(
            self,
            "load-or-create-iot-credentials",
            service_token=aws_ssm.StringParameter.from_string_parameter_name(
                self,
                "load-or-create-iot-credentials-lambda-arn",
                f"/{VPConstants.STAGE}/{VPConstants.APP_NAME}/arns/custom-resource-lambda-arn",
            ).string_value,
            resource_type=f"Custom::{CustomResourceType.ResourceType.LOAD_OR_CREATE_IOT_CREDENTIALS.value}",
            properties={
                "Resource": CustomResourceType.ResourceType.LOAD_OR_CREATE_IOT_CREDENTIALS.value,
                "IoTCredentialsSecretId": provisioning_secret_id,
                "RotateSecretLambdaARN": aws_ssm.StringParameter.from_string_parameter_name(
                    self,
                    "rotate-secret-lambda-arn-value",
                    f"/{VPConstants.STAGE}/{VPConstants.APP_NAME}/arns/rotate-secret-lambda-arn",
                ).string_value,
            },
        )

        CustomResource(
            self,
            "update-event-configurations",
            service_token=aws_ssm.StringParameter.from_string_parameter_name(
                self,
                "update-event-configurations-lambda-arn",
                f"/{VPConstants.STAGE}/{VPConstants.APP_NAME}/arns/custom-resource-lambda-arn",
            ).string_value,
            resource_type=f"Custom::{CustomResourceType.ResourceType.UPDATE_EVENT_CONFIGURATIONS.value}",
            properties={
                "Resource": CustomResourceType.ResourceType.UPDATE_EVENT_CONFIGURATIONS.value
            },
        )

        # Upload and register vehicle simulator claim certificate.
        provisioning_claim_certificate = aws_iot.CfnCertificate(
            self,
            "provisioning-claim-certificate",
            status="ACTIVE",
            certificate_mode="SNI_ONLY",
            certificate_pem=self.iot_credentials.get_att("CERTIFICATE_PEM").to_string(),
        )

        # Create IoT policy, which would permit a client with this claim certificate to request new credentials.
        aws_iot.CfnPolicy(
            self,
            "claim-certificate-provisioning-policy",
            policy_document=aws_iam.PolicyDocument(
                statements=[
                    aws_iam.PolicyStatement(
                        effect=aws_iam.Effect.ALLOW,
                        actions=[
                            "iot:Connect",
                        ],
                        resources=[
                            "*",  # NOSONAR
                        ],  # These actions require a wildcard resource
                    ),
                    aws_iam.PolicyStatement(
                        effect=aws_iam.Effect.ALLOW,
                        actions=[
                            "iot:Publish",
                            "iot:Receive",
                        ],
                        resources=[
                            Stack.of(self).format_arn(
                                service="iot",
                                resource="topic",
                                resource_name="$aws/certificates/create/*",
                                arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                            ),
                            Stack.of(self).format_arn(
                                service="iot",
                                resource="topic",
                                resource_name=f"$aws/provisioning-templates/{VPConstants.PROVISIONING_TEMPLATE_NAME}/provision/*",
                                arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                            ),
                        ],
                    ),
                    aws_iam.PolicyStatement(
                        effect=aws_iam.Effect.ALLOW,
                        actions=[
                            "iot:Subscribe",
                        ],
                        resources=[
                            Stack.of(self).format_arn(
                                service="iot",
                                resource="topicfilter",
                                resource_name="$aws/certificates/create/*",
                                arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                            ),
                            Stack.of(self).format_arn(
                                service="iot",
                                resource="topicfilter",
                                resource_name=f"$aws/provisioning-templates/{VPConstants.PROVISIONING_TEMPLATE_NAME}/provision/*",
                                arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                            ),
                        ],
                    ),
                ],
            ),
            policy_name=VPConstants.CLAIM_CERT_PROVISIONING_POLICY_NAME,
        )

        # Attach policy to certificate
        aws_iot.CfnPolicyPrincipalAttachment(
            self,
            "claim-certificate-provisioning-policy-principal-attachment",
            policy_name=VPConstants.CLAIM_CERT_PROVISIONING_POLICY_NAME,
            principal=provisioning_claim_certificate.attr_arn,
        )

        CustomResource(
            self,
            "delete-provisioning-certificate",
            service_token=aws_ssm.StringParameter.from_string_parameter_name(
                self,
                "delete-provisioning-certificate-lambda-arn",
                f"/{VPConstants.STAGE}/{VPConstants.APP_NAME}/arns/custom-resource-lambda-arn",
            ).string_value,
            resource_type=f"Custom::{CustomResourceType.ResourceType.DELETE_PROVISIONING_CERTIFICATE.value}",
            properties={
                "Resource": CustomResourceType.ResourceType.DELETE_PROVISIONING_CERTIFICATE.value,
                "IoTPolicyName": VPConstants.CLAIM_CERT_PROVISIONING_POLICY_NAME,
            },
        )

        # Provisioning credentials SecretsManager ID
        CfnOutput(
            self,
            "provisioning-credentials-secret-id",
            description="AWS Secrets Manager secret id for provisioning credentials.",
            value=provisioning_secret_id,
        )
