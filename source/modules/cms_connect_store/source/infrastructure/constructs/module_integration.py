# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any

# AWS Libraries
from aws_cdk import Stack, aws_s3, aws_ssm
from constructs import Construct

# CMS Common Library
from cms_common.config.resource_names import ResourceName, ResourcePrefix
from cms_common.config.stack_inputs import SolutionConfigInputs
from cms_common.constructs.app_unique_id import AppUniqueId
from cms_common.constructs.encrypted_s3 import EncryptedS3Construct
from cms_common.constructs.identity_provider_config import IdentityProviderConfig
from cms_common.constructs.vpc_construct import create_vpc_config, get_vpc_name
from cms_common.resource_names.module_short_names import CMSModuleShortNames

# Connected Mobility Solution on AWS
from .s3_to_glue import GlueResources


class ModuleInputsConstruct(Construct):
    def __init__(self, scope: Construct, construct_id: str, **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.app_unique_id = AppUniqueId.create_cfn_parameter(Stack.of(self))

        self.identity_provider_id = IdentityProviderConfig.get_identity_provider_id(
            scope=self, app_unique_id=self.app_unique_id
        )

        self.vpc_config = create_vpc_config(
            vpc_name=get_vpc_name(scope=self, app_unique_id=self.app_unique_id)
        )

        self.alerts_publish_endpoint_ssm_path = ResourceName.slash_separated(
            prefix=ResourcePrefix.slash_separated(
                app_unique_id=self.app_unique_id,
                module_name=CMSModuleShortNames.ALERTS,
                leading_slash=True,
            ),
            name="publish-api/endpoint",
        )

        self.s3_log_lifecycle_rules = (
            EncryptedS3Construct.create_log_lifecycle_cfn_parameters(self)
        )


class ModuleOutputsConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_unique_id: str,
        solution_config_inputs: SolutionConfigInputs,
        glue_catalog_name: str,
        glue_resources: GlueResources,
        root_s3_bucket: aws_s3.Bucket,
    ) -> None:
        super().__init__(scope, construct_id)

        ssm_parameter_name_prefix_with_leading_slash = ResourcePrefix.slash_separated(
            app_unique_id=app_unique_id,
            module_name=solution_config_inputs.module_short_name,
            leading_slash=True,
        )

        # Export SSM parameters for resources created in this stack
        aws_ssm.StringParameter(
            self,
            "ssm-telemetry-glue-data-catalog",
            description="The Glue data catalog in which the table is to be created.",
            parameter_name=ResourceName.slash_separated(
                prefix=ssm_parameter_name_prefix_with_leading_slash,
                name="glue-data-catalog/name",
            ),
            string_value=glue_catalog_name,
            simple_name=False,
        )
        aws_ssm.StringParameter(
            self,
            "ssm-telemetry-glue-database",
            description="The Glue database in which the telemetry table is stored.",
            parameter_name=ResourceName.slash_separated(
                prefix=ssm_parameter_name_prefix_with_leading_slash,
                name="glue-database/name",
            ),
            string_value=glue_resources.glue_database.database_input.name,  # type: ignore [union-attr, arg-type]
            simple_name=False,
        )
        aws_ssm.StringParameter(
            self,
            "ssm-telemetry-glue-table",
            description="The Glue table which references to the stored telemetry data.",
            parameter_name=ResourceName.slash_separated(
                prefix=ssm_parameter_name_prefix_with_leading_slash,
                name="glue-table/name",
            ),
            string_value=glue_resources.glue_table.table_input.name,  # type: ignore [union-attr, arg-type]
            simple_name=False,
        )
        aws_ssm.StringParameter(
            self,
            "ssm-glue-schema-arn",
            description="CMS Connect and Store AWS Glue Schema Arn",
            parameter_name=ResourceName.slash_separated(
                prefix=ssm_parameter_name_prefix_with_leading_slash,
                name="glue-schema/arn",
            ),
            string_value=glue_resources.glue_schema.attr_arn,
            simple_name=False,
        )
        aws_ssm.StringParameter(
            self,
            "ssm-glue-registry-name",
            description="CMS Connect and Store AWS Glue Registry Name",
            parameter_name=ResourceName.slash_separated(
                prefix=ssm_parameter_name_prefix_with_leading_slash,
                name="glue-registry/name",
            ),
            string_value=glue_resources.glue_schema.registry.name,  # type: ignore [union-attr, arg-type]
            simple_name=False,
        )
        aws_ssm.StringParameter(
            self,
            "ssm-telemetry-storage-bucket-region",
            description="The region of the S3 bucket in which the telemetry data is stored.",
            parameter_name=ResourceName.slash_separated(
                prefix=ssm_parameter_name_prefix_with_leading_slash,
                name="s3-storage-bucket/region",
            ),
            string_value=Stack.of(self).region,
            simple_name=False,
        )
        aws_ssm.StringParameter(
            self,
            "ssm-telemetry-storage-bucket-name",
            description="The name of the S3 bucket in which the telemetry data is stored.",
            parameter_name=ResourceName.slash_separated(
                prefix=ssm_parameter_name_prefix_with_leading_slash,
                name="s3-storage-bucket/name",
            ),
            string_value=root_s3_bucket.bucket_name,
            simple_name=False,
        )
        aws_ssm.StringParameter(
            self,
            "ssm-telemetry-storage-bucket-arn",
            description="The ARN of the S3 bucket in which the telemetry data is stored.",
            parameter_name=ResourceName.slash_separated(
                prefix=ssm_parameter_name_prefix_with_leading_slash,
                name="s3-storage-bucket/arn",
            ),
            string_value=root_s3_bucket.bucket_arn,
            simple_name=False,
        )
