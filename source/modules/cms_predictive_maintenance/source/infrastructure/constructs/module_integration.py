# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
# Standard Library
from dataclasses import dataclass

# AWS Libraries
from aws_cdk import Stack, aws_ssm
from constructs import Construct

# CMS Common Library
from cms_common.config.resource_names import ResourceName, ResourcePrefix
from cms_common.config.ssm import resolve_ssm_parameter
from cms_common.config.stack_inputs import SolutionConfigInputs
from cms_common.constructs.app_unique_id import AppUniqueId
from cms_common.constructs.encrypted_s3 import EncryptedS3Construct
from cms_common.constructs.vpc_construct import create_vpc_config, get_vpc_name
from cms_common.resource_names.auth import AuthResourceNames

# Connected Mobility Solution on AWS
from .api.interface import PredictApiOutputs
from .chatbot.interface import ChatbotConstructOutputs
from .predictor.interface import PredictorConstructOutputs


@dataclass(frozen=True)
class TokenValidationInputs:
    lambda_arn: str


class ModuleInputsConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
    ) -> None:
        super().__init__(scope, construct_id)

        self.app_unique_id = AppUniqueId.create_cfn_parameter(Stack.of(self))

        self.vpc_config = create_vpc_config(
            vpc_name=get_vpc_name(scope=self, app_unique_id=self.app_unique_id)
        )

        self.token_validation = TokenValidationInputs(
            lambda_arn=resolve_ssm_parameter(
                parameter_name=AuthResourceNames.from_app_unique_id(
                    app_unique_id=self.app_unique_id
                ).token_validation_lambda_arn,
            ),
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
        chatbot_construct_outputs: ChatbotConstructOutputs,
        predictor_construct_outputs: PredictorConstructOutputs,
        predict_api_outputs: PredictApiOutputs,
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
            "ssm-chatbot-knowledge-base-id",
            description="The Bedrock knowledge base ID used for RAG.",
            parameter_name=ResourceName.slash_separated(
                prefix=ssm_parameter_name_prefix_with_leading_slash,
                name="chatbot/knowledge-base-id",
            ),
            string_value=chatbot_construct_outputs.knowledge_base_id,
            simple_name=False,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-chatbot-agent-id",
            description="The Bedrock agent ID.",
            parameter_name=ResourceName.slash_separated(
                prefix=ssm_parameter_name_prefix_with_leading_slash,
                name="chatbot/agent-id",
            ),
            string_value=chatbot_construct_outputs.agent_id,
            simple_name=False,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-chatbot-agent-alias-id",
            description="The Bedrock agent alias ID.",
            parameter_name=ResourceName.slash_separated(
                prefix=ssm_parameter_name_prefix_with_leading_slash,
                name="chatbot/agent-alias-id",
            ),
            string_value=chatbot_construct_outputs.agent_alias_id,
            simple_name=False,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-predictor-pipeline-role-arn",
            description="The ARN of the role for the SageMaker pipeline.",
            parameter_name=ResourceName.slash_separated(
                prefix=ssm_parameter_name_prefix_with_leading_slash,
                name="predictor/pipeline/role-arn",
            ),
            string_value=predictor_construct_outputs.pipeline_role_arn,
            simple_name=False,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-predictor-pipeline-assets-bucket-name",
            description="The name of the S3 bucket created for the SageMaker pipeline.",
            parameter_name=ResourceName.slash_separated(
                prefix=ssm_parameter_name_prefix_with_leading_slash,
                name="predictor/pipeline/assets-bucket/name",
            ),
            string_value=predictor_construct_outputs.pipeline_assets_bucket_name,
            simple_name=False,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-predictor-pipeline-deploy-model-lambda-function-arn",
            description="ARN of the lambda function used to deploy SageMaker model to a SageMaker endpoint.",
            parameter_name=ResourceName.slash_separated(
                prefix=ssm_parameter_name_prefix_with_leading_slash,
                name="predictor/pipeline/deploy-model-lambda/arn",
            ),
            string_value=predictor_construct_outputs.deploy_model_lambda_function_arn,
            simple_name=False,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-predictor-pipeline-deploy-model-endpoint-name",
            description="Name of the SageMaker endpoint to which the SageMaker prediction model is deployed.",
            parameter_name=ResourceName.slash_separated(
                prefix=ssm_parameter_name_prefix_with_leading_slash,
                name="predictor/pipeline/deploy-model-endpoint/name",
            ),
            string_value=predictor_construct_outputs.deploy_model_endpoint_name,
            simple_name=False,
        )

        aws_ssm.StringParameter(
            self,
            "ssm-predict-api-endpoint-url",
            description="URL of the endpoint for the Predict APIs exposed by the module.",
            parameter_name=ResourceName.slash_separated(
                prefix=ssm_parameter_name_prefix_with_leading_slash,
                name="api/predict/endpoint/url",
            ),
            string_value=predict_api_outputs.endpoint_url,
            simple_name=False,
        )
