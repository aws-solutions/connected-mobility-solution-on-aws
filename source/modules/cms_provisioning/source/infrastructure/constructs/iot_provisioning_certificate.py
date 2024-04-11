# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library

# AWS Libraries
from aws_cdk import ArnFormat, CustomResource, Stack, aws_iam, aws_iot
from constructs import Construct

# CMS Common Library
from cms_common.constructs.custom_resource_lambda import CustomResourceLambdaConstruct

# Connected Mobility Solution on AWS
from ...handlers.custom_resource.function.lib.custom_resource_type_enum import (
    CustomResourceFunctionType,
)


class IoTProvisioningCertificateConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        custom_resource_lambda_construct: CustomResourceLambdaConstruct,
        iot_credentials: str,
        provisioning_template_name: str,
        claim_cert_provisioning_policy_name: str,
    ) -> None:
        super().__init__(scope, construct_id)

        # Upload and register vehicle simulator claim certificate.
        provisioning_claim_certificate = aws_iot.CfnCertificate(
            self,
            "claim-certificate",
            status="ACTIVE",
            certificate_mode="SNI_ONLY",
            certificate_pem=iot_credentials,
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
                                resource_name=f"$aws/provisioning-templates/{provisioning_template_name}/provision/*",
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
                                resource_name=f"$aws/provisioning-templates/{provisioning_template_name}/provision/*",
                                arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                            ),
                        ],
                    ),
                ],
            ),
            policy_name=claim_cert_provisioning_policy_name,
        )

        # Attach policy to certificate
        aws_iot.CfnPolicyPrincipalAttachment(
            self,
            "claim-certificate-provisioning-policy-principal-attachment",
            policy_name=claim_cert_provisioning_policy_name,
            principal=provisioning_claim_certificate.attr_arn,
        )

        provisioning_certificate_custom_resource_policy = aws_iam.Policy(
            self,
            "custom-resource-policy",
            statements=[
                aws_iam.PolicyStatement(
                    actions=["iot:DeleteCertificate", "iot:UpdateCertificate"],
                    effect=aws_iam.Effect.ALLOW,
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
                    actions=[
                        "iot:ListTargetsForPolicy",
                        "iot:DetachPolicy",
                    ],
                    effect=aws_iam.Effect.ALLOW,
                    resources=[
                        Stack.of(self).format_arn(
                            service="iot",
                            resource="policy",
                            resource_name=claim_cert_provisioning_policy_name,
                            arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                        ),
                        Stack.of(self).format_arn(
                            service="iot",
                            resource="cert",
                            resource_name="*",
                            arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                        ),
                    ],
                ),
            ],
        )
        custom_resource_lambda_construct.add_policy_to_custom_resource_lambda(
            policy=provisioning_certificate_custom_resource_policy,
        )

        delete_provisioning_certificate = CustomResource(
            self,
            "delete-provisioning-certificate",
            service_token=custom_resource_lambda_construct.function.function_arn,
            resource_type=f"Custom::{CustomResourceFunctionType.DELETE_PROVISIONING_CERTIFICATE.value}",
            properties={
                "Resource": CustomResourceFunctionType.DELETE_PROVISIONING_CERTIFICATE.value,
                "IoTPolicyName": claim_cert_provisioning_policy_name,
            },
        )
        delete_provisioning_certificate.node.add_dependency(
            provisioning_certificate_custom_resource_policy
        )
