# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import cast

# AWS Libraries
from aws_cdk import CfnParameter, CfnResource, Stack, aws_ssm
from constructs import Construct

# CMS Common Library
from cms_common.config.resource_names import ResourceName, remove_leading_slash
from cms_common.constructs.app_unique_id import AppUniqueId
from cms_common.constructs.custom_resource_lambda import CustomResourceLambdaConstruct
from cms_common.constructs.identity_provider_config import IdentityProviderConfig
from cms_common.constructs.vpc_construct import VpcConfig, create_vpc_config
from cms_common.resource_names.config import ConfigResourceNames

# Connected Mobility Solution on AWS
from .metrics import MetricsConstruct


class ModuleInputsConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
    ) -> None:
        super().__init__(scope, construct_id)

        self.app_unique_id = AppUniqueId.create_cfn_parameter(Stack.of(self))
        self.identity_provider_id = IdentityProviderConfig.create_cfn_parameter(
            Stack.of(self)
        )

        self.vpc_config = create_vpc_config(
            CfnParameter(Stack.of(self), "VpcName").value_as_string
        )


class ModuleOutputsConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        deployment_uuid: str,
        module_inputs_construct: ModuleInputsConstruct,
        metrics_url: str,
        metrics_construct: MetricsConstruct,
        vpc_config: VpcConfig,
        vpc_name_provider_construct: CustomResourceLambdaConstruct,
    ) -> None:
        super().__init__(scope, construct_id)

        app_unique_id = module_inputs_construct.app_unique_id
        config_resource_names = ConfigResourceNames.from_app_unique_id(app_unique_id)
        ssm_prefix_with_leading_slash = config_resource_names.config_prefix
        self.ssm_prefix_without_leading_slash = remove_leading_slash(
            config_resource_names.config_prefix
        )

        aws_ssm.StringParameter(
            self,
            "ssm-deployment-uuid",
            string_value=deployment_uuid,
            description=f"Deployment UUID associated with app unique ID - {app_unique_id}",
            parameter_name=ResourceName.slash_separated(
                prefix=ssm_prefix_with_leading_slash, name="deployment-uuid"
            ),
            simple_name=True,
        )

        aws_ssm.StringParameter(
            self,
            "identity-provider-id",
            string_value=module_inputs_construct.identity_provider_id,
            description=f"Identity Provider ID associated with app unique ID - {app_unique_id}",
            parameter_name=config_resource_names.identity_provider_id_ssm_parameter,
            simple_name=True,
        )

        aws_ssm.StringParameter(
            self,
            "vpc-name",
            string_value=vpc_config.vpc_name,
            description="VPC Name",
            parameter_name=config_resource_names.vpc_name_ssm_parameter,
            simple_name=True,
        )

        aws_ssm.StringParameter(
            self,
            "aws-resource-lookup-lambda-arn",
            string_value=vpc_name_provider_construct.function.function_arn,
            description="Arn of AWS resource lookup Lambda function",
            parameter_name=config_resource_names.aws_resource_lookup_lambda_arn_ssm_parameter,
            simple_name=True,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-anonymous-metrics-enabled",
            string_value=metrics_construct.send_anonymous_usage,
            description=f"Anonymous metrics enabled or not for app unique ID - {app_unique_id}",
            parameter_name=ResourceName.slash_separated(
                prefix=ssm_prefix_with_leading_slash, name="metrics/enabled"
            ),
            simple_name=True,
        )

        metrics_parameter = aws_ssm.StringParameter(
            self,
            "ssm-anonymous-metrics-url",
            string_value=metrics_url,
            description=f"URL to send anonymous metrics to for app unique ID - {app_unique_id}",
            parameter_name=ResourceName.slash_separated(
                prefix=ssm_prefix_with_leading_slash, name="metrics/url"
            ),
            simple_name=True,
        )

        metrics_cfn_resource: CfnResource = cast(
            CfnResource, metrics_parameter.node.default_child
        )
        metrics_cfn_resource.cfn_options.condition = (
            metrics_construct.send_anonymous_usage_condition
        )
