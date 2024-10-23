# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
from os.path import abspath, dirname
from typing import Any

# Third Party Libraries
import yaml

# AWS Libraries
from aws_cdk import CfnMapping, Stack, Tags
from constructs import Construct

# CMS Common Library
from cms_common.config.ssm import get_resolvable_ssm_deployment_uuid
from cms_common.config.stack_inputs import S3AssetConfigInputs, SolutionConfigInputs
from cms_common.constructs.app_unique_id import AppUniqueId
from cms_common.constructs.cdk_lambda_vpc_config_construct import (
    CDKLambdasVpcConfigConstruct,
)
from cms_common.constructs.cmk_encrypted_s3 import CMKEncryptedS3Construct
from cms_common.constructs.custom_resource_lambda import CustomResourceLambdaConstruct
from cms_common.constructs.lambda_dependencies import LambdaDependenciesConstruct
from cms_common.constructs.vpc_construct import VpcConstruct

# Connected Mobility Solution on AWS
from .constructs.agent_action_group import AgentActionGroupConstruct
from .constructs.api.authorization_lambda import AuthorizationLambdaConstruct
from .constructs.api.interface import BatchInferenceConfig
from .constructs.api.predict_api import PredictApiConstruct
from .constructs.chatbot.chatbot import ChatbotConstruct
from .constructs.chatbot.interface import (
    AgentConfig,
    DataSourceChunkingConfig,
    EmbeddingModelConfig,
    S3DataSourceConfig,
    VectorConfig,
    VectorIndexConfig,
    VectorMethod,
)
from .constructs.module_integration import ModuleInputsConstruct, ModuleOutputsConstruct
from .constructs.predictor.predictor import PredictorConstruct


class CmsPredictiveMaintenanceStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        solution_config_inputs: SolutionConfigInputs,
        s3_asset_config_inputs: S3AssetConfigInputs,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        CfnMapping(
            self,
            "Solution",
            mapping={
                "AssetsConfig": {
                    "S3AssetBucketBaseName": s3_asset_config_inputs.bucket_base_name,
                    "S3AssetKeyPrefix": s3_asset_config_inputs.object_key_prefix,
                },
            },
        )

        # NOTE: AppRegistryConstruct is commented out now because the tag added by this construct is
        # exceeding the length limit of tags supported by the aws_sagemaker.CfnDomain resource.
        # AppRegistryConstruct(
        #     self,
        #     "app-registry-construct",
        #     app_registry_inputs=AppRegistryInputs(
        #         application_name=Aws.STACK_NAME,
        #         application_type=solution_config_inputs.application_type,
        #         solution_id=solution_config_inputs.solution_id,
        #         solution_name=solution_config_inputs.solution_name,
        #         solution_version=solution_config_inputs.solution_version,
        #     ),
        # )

        module_inputs_construct = ModuleInputsConstruct(self, "module-inputs-construct")
        app_unique_id = module_inputs_construct.app_unique_id

        # Check if a config stack for the app unique id is registered. Fail stack
        # creation if it is not registered. If config stack exists, then create an SSM
        # parameter to register the module with the app unique id.
        register_module_with_app_unique_id = AppUniqueId.register_module(
            self,
            app_unique_id=app_unique_id,
            module_name=solution_config_inputs.module_short_name,
        )

        deployment_uuid = get_resolvable_ssm_deployment_uuid(
            app_unique_id=app_unique_id
        )

        self.cms_predictive_maintenance_construct = CmsPredictiveMaintenanceConstruct(
            self,
            "cms-predictive-maintenance",
            solution_config_inputs=solution_config_inputs,
            module_inputs_construct=module_inputs_construct,
        )
        self.cms_predictive_maintenance_construct.node.add_dependency(
            register_module_with_app_unique_id
        )

        Tags.of(self.cms_predictive_maintenance_construct).add(
            "Solutions:DeploymentUUID", deployment_uuid
        )


class CmsPredictiveMaintenanceConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        solution_config_inputs: SolutionConfigInputs,
        module_inputs_construct: ModuleInputsConstruct,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        config_file_path = f"{os.getcwd()}/source/config.yaml"
        with open(config_file_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        vpc_construct = VpcConstruct(
            self, "vpc-construct", vpc_config=module_inputs_construct.vpc_config
        )

        self.cdk_lambdas_vpc_construct = CDKLambdasVpcConfigConstruct(
            self,
            "cdk-lambdas-vpc-construct",
            vpc_construct=vpc_construct,
            subnets=module_inputs_construct.vpc_config.private_subnets,
        )

        lambda_dependencies_construct = LambdaDependenciesConstruct(
            self,
            "dependency-layer-construct",
            pipfile_path=f"{dirname(dirname(dirname(abspath(__file__))))}/Pipfile",
            dependency_layer_path=f"{os.getcwd()}/source/infrastructure/cms_predictive_maintenance_dependency_layer",
        )

        custom_resource_lambda_construct = CustomResourceLambdaConstruct(
            self,
            "custom-resource-lambda-construct",
            dependency_layer=lambda_dependencies_construct.dependency_layer,
            unique_id=module_inputs_construct.app_unique_id,
            name=solution_config_inputs.module_short_name,
            asset_path="dist/lambda/custom_resource.zip",
            user_agent_string=solution_config_inputs.get_user_agent_string(),
            vpc_construct=vpc_construct,
        )

        sagemaker_assets_bucket_construct = CMKEncryptedS3Construct(
            self,
            "sagemaker-assets-bucket-construct",
        )

        predictor_construct = PredictorConstruct(
            self,
            "predictor-construct",
            app_unique_id=module_inputs_construct.app_unique_id,
            solution_config_inputs=solution_config_inputs,
            vpc_construct=vpc_construct,
            custom_resource_lambda_construct=custom_resource_lambda_construct,
            dependency_layer=lambda_dependencies_construct.dependency_layer,
            sagemaker_assets_bucket_construct=sagemaker_assets_bucket_construct,
        )

        agent_action_group_construct = AgentActionGroupConstruct(
            self,
            "agent-action-group-construct",
            app_unique_id=module_inputs_construct.app_unique_id,
            solution_config_inputs=solution_config_inputs,
            dependency_layer=lambda_dependencies_construct.dependency_layer,
            vpc_construct=vpc_construct,
            sagemaker_assets_bucket_construct=sagemaker_assets_bucket_construct,
            inference_data_s3_key_prefix=config["predictor"]["inference"]["batch"][
                "data_s3_key_prefix"
            ],
        )

        chatbot_construct = ChatbotConstruct(
            self,
            "chatbot-construct",
            module_inputs_construct=module_inputs_construct,
            solution_config_inputs=solution_config_inputs,
            custom_resource_lambda_construct=custom_resource_lambda_construct,
            embedding_model_inputs=EmbeddingModelConfig(
                model_name=config["chatbot"]["embedding"]["model_name"]
            ),
            s3_data_source_inputs=S3DataSourceConfig(
                bucket_name=config["chatbot"]["data_source"]["s3"]["bucket_name"],
                object_key_prefix=config["chatbot"]["data_source"]["s3"][
                    "object_key_prefix"
                ],
                bucket_owner_account_id=Stack.of(self).account,
            ),
            data_source_chunking_config=DataSourceChunkingConfig(
                strategy=config["chatbot"]["data_source"]["chunking_configuration"][
                    "strategy"
                ],
                max_tokens=config["chatbot"]["data_source"]["chunking_configuration"][
                    "max_tokens"
                ],
                overlap_percentage=config["chatbot"]["data_source"][
                    "chunking_configuration"
                ]["overlap_percentage"],
            ),
            vector_index_config=VectorIndexConfig(
                name=config["chatbot"]["vector_index"]["name"],
                vector=VectorConfig(
                    name=config["chatbot"]["vector_index"]["vector"]["name"],
                    metadata_field=config["chatbot"]["vector_index"]["vector"][
                        "metadata_field"
                    ],
                    text_field=config["chatbot"]["vector_index"]["vector"][
                        "text_field"
                    ],
                    vector_type=config["chatbot"]["vector_index"]["vector"]["type"],
                    dimension=config["chatbot"]["vector_index"]["vector"]["dimension"],
                    method=VectorMethod(
                        name=config["chatbot"]["vector_index"]["vector"]["method"][
                            "name"
                        ],
                        space_type=config["chatbot"]["vector_index"]["vector"][
                            "method"
                        ]["space_type"],
                        engine=config["chatbot"]["vector_index"]["vector"]["method"][
                            "engine"
                        ],
                        ef_construction=config["chatbot"]["vector_index"]["vector"][
                            "method"
                        ]["ef_construction"],
                        m=config["chatbot"]["vector_index"]["vector"]["method"]["m"],
                    ),
                ),
            ),
            agent_config=AgentConfig(
                instruction=config["chatbot"]["agent"]["instruction"],
                foundational_model_id=config["chatbot"]["agent"]["model_id"],
                idle_session_ttl_in_seconds=config["chatbot"]["agent"][
                    "session_retention_time_seconds"
                ],
            ),
            agent_action_groups=[agent_action_group_construct.action_group],
        )

        authorization_lambda_construct = AuthorizationLambdaConstruct(  # nosec
            self,
            "authorization-lambda-construct",
            app_unique_id=module_inputs_construct.app_unique_id,
            solution_config_inputs=solution_config_inputs,
            dependency_layer=lambda_dependencies_construct.dependency_layer,
            token_validation_lambda_arn=module_inputs_construct.token_validation.lambda_arn,
            vpc_construct=vpc_construct,
        )

        predict_api_construct = PredictApiConstruct(
            self,
            "predict-api-construct",
            app_unique_id=module_inputs_construct.app_unique_id,
            solution_config_inputs=solution_config_inputs,
            dependency_layer=lambda_dependencies_construct.dependency_layer,
            vpc_construct=vpc_construct,
            authorization_lambda_construct=authorization_lambda_construct,
            sagemaker_model_endpoint_name=predictor_construct.outputs.deploy_model_endpoint_name,
            sagemaker_assets_bucket_construct=sagemaker_assets_bucket_construct,
            batch_inference_config=BatchInferenceConfig(
                data_s3_key_prefix=config["predictor"]["inference"]["batch"][
                    "data_s3_key_prefix"
                ],
                instance_type=config["predictor"]["inference"]["batch"][
                    "instance_type"
                ],
                instance_count=config["predictor"]["inference"]["batch"][
                    "instance_count"
                ],
            ),
        )

        ModuleOutputsConstruct(
            self,
            "module-outputs-construct",
            app_unique_id=module_inputs_construct.app_unique_id,
            solution_config_inputs=solution_config_inputs,
            chatbot_construct_outputs=chatbot_construct.outputs,
            predictor_construct_outputs=predictor_construct.outputs,
            predict_api_outputs=predict_api_construct.outputs,
        )
