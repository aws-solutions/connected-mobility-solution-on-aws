# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
# Standard Library
import os

# AWS Libraries
from sagemaker import PipelineModel
from sagemaker.inputs import TrainingInput
from sagemaker.model_metrics import MetricsSource, ModelMetrics
from sagemaker.processing import FrameworkProcessor, ProcessingInput, ProcessingOutput
from sagemaker.pytorch import PyTorch, PyTorchModel
from sagemaker.sklearn.processing import SKLearnProcessor
from sagemaker.workflow.condition_step import ConditionStep
from sagemaker.workflow.conditions import ConditionGreaterThanOrEqualTo
from sagemaker.workflow.functions import JsonGet
from sagemaker.workflow.lambda_step import Lambda, LambdaStep
from sagemaker.workflow.model_step import ModelStep
from sagemaker.workflow.parameters import (
    ParameterFloat,
    ParameterInteger,
    ParameterString,
)
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.pipeline_context import PipelineSession
from sagemaker.workflow.properties import PropertyFile
from sagemaker.workflow.steps import CacheConfig, ProcessingStep, TrainingStep

PYTORCH_FRAMEWORK_VERSION = "2.2.0"
SKLEARN_FRAMEWORK_VERSION = "1.2-1"
PYTHON_VERSION = "py310"
PIPELINE_CACHE_EXPIRATION = "T12h"  # 12 hours

DEFAULT_PREPROCESSING_INSTANCE_TYPE = "ml.m5.large"
DEFAULT_PREPROCESSING_INSTANCE_COUNT = 1

DEFAULT_TRAINING_INSTANCE_TYPE = "ml.c5.2xlarge"
DEFAULT_TRAINING_INSTANCE_COUNT = 1
DEFAULT_TRAINING_HYPERPARAMETER_NUM_EPOCHS = 100
DEFAULT_TRAINING_HYPERPARAMETER_BATCH_SIZE = 32
DEFAULT_TRAINING_HYPERPARAMETER_LEARNING_RATE = 0.001

DEFAULT_EVALUATION_INSTANCE_TYPE = "ml.m5.xlarge"
DEFAULT_EVALUATION_INSTANCE_COUNT = 1

DEFAULT_MODEL_ACCURACY_THRESHOLD = 0.6

DEFAULT_REAL_TIME_INFERENCE_INSTANCE_TYPE = "ml.m5.large"
DEFAULT_REAL_TIME_INFERENCE_INSTANCE_COUNT = 1
DEFAULT_BATCH_TRANSFORM_INFERENCE_INSTANCE_TYPE = "ml.m5.xlarge"


def create_predictive_maintenance_pipeline(  # pylint: disable=too-many-locals
    pipeline_name: str,
    pipeline_role_arn: str,
    pipeline_assets_bucket_name: str,
    deploy_model_function_arn: str,
    endpoint_name: str,
    resource_name_suffix: str,
) -> Pipeline:
    # session configuration
    pipeline_session = PipelineSession(default_bucket=pipeline_assets_bucket_name)
    cache_config = CacheConfig(
        enable_caching=True, expire_after=PIPELINE_CACHE_EXPIRATION
    )

    # pipeline input parameters
    raw_dataset_s3_uri = ParameterString(name="RawDatasetS3Uri")
    preprocessing_instance_type = ParameterString(
        name="PreprocessingInstanceType",
        default_value=DEFAULT_PREPROCESSING_INSTANCE_TYPE,
    )
    preprocessing_instance_count = ParameterInteger(
        name="PreprocessingInstanceCount",
        default_value=DEFAULT_PREPROCESSING_INSTANCE_COUNT,
    )
    training_instance_type = ParameterString(
        name="TrainingInstanceType",
        default_value=DEFAULT_TRAINING_INSTANCE_TYPE,
    )
    training_instance_count = ParameterInteger(
        name="TrainingInstanceCount",
        default_value=DEFAULT_TRAINING_INSTANCE_COUNT,
    )
    training_hyperparameter_num_epochs = ParameterInteger(
        name="TrainingHyperParameterNumEpochs",
        default_value=DEFAULT_TRAINING_HYPERPARAMETER_NUM_EPOCHS,
    )
    training_hyperparameter_batch_size = ParameterInteger(
        name="TrainingHyperParameterBatchSize",
        default_value=DEFAULT_TRAINING_HYPERPARAMETER_BATCH_SIZE,
    )
    training_hyperparameter_learning_rate = ParameterFloat(
        name="TrainingHyperParameterLearningRate",
        default_value=DEFAULT_TRAINING_HYPERPARAMETER_LEARNING_RATE,
    )
    evaluation_instance_type = ParameterString(
        name="EvaluationInstanceType",
        default_value=DEFAULT_EVALUATION_INSTANCE_TYPE,
    )
    evaluation_instance_count = ParameterInteger(
        name="EvaluationInstanceCount",
        default_value=DEFAULT_EVALUATION_INSTANCE_COUNT,
    )
    model_accuracy_threshold = ParameterFloat(
        name="ModelAccuracyThreshold",
        default_value=DEFAULT_MODEL_ACCURACY_THRESHOLD,
    )
    real_time_inference_instance_type = ParameterString(
        name="RealTimeInferenceInstanceType",
        default_value=DEFAULT_REAL_TIME_INFERENCE_INSTANCE_TYPE,
    )
    real_time_inference_instance_count = ParameterInteger(
        name="RealTimeInferenceInstanceCount",
        default_value=DEFAULT_REAL_TIME_INFERENCE_INSTANCE_COUNT,
    )
    batch_transform_inference_instance_type = ParameterString(
        name="BatchTransformInferenceInstanceType",
        default_value=DEFAULT_BATCH_TRANSFORM_INFERENCE_INSTANCE_TYPE,
    )

    # preprocessing step
    sklearn_processor = SKLearnProcessor(
        framework_version=SKLEARN_FRAMEWORK_VERSION,
        instance_type=preprocessing_instance_type,
        instance_count=preprocessing_instance_count,
        sagemaker_session=pipeline_session,
        role=pipeline_role_arn,
    )
    preprocessing_files_base_dir = "/opt/ml/processing"
    pipeline_steps_source_dir = (
        f"{os.path.dirname(os.path.realpath(__file__))}/pipeline_steps"
    )
    processor_args = sklearn_processor.run(
        inputs=[
            ProcessingInput(
                source=raw_dataset_s3_uri,
                destination=f"{preprocessing_files_base_dir}/input",
            ),
        ],
        outputs=[
            ProcessingOutput(
                output_name="train", source=f"{preprocessing_files_base_dir}/train"
            ),
            ProcessingOutput(
                output_name="validation",
                source=f"{preprocessing_files_base_dir}/validation",
            ),
            ProcessingOutput(
                output_name="test", source=f"{preprocessing_files_base_dir}/test"
            ),
        ],
        code=f"{pipeline_steps_source_dir}/preprocess.py",
    )
    step_process = ProcessingStep(
        name="Preprocess", step_args=processor_args, cache_config=cache_config
    )

    # training step
    estimator = PyTorch(
        role=pipeline_role_arn,
        py_version=PYTHON_VERSION,
        framework_version=PYTORCH_FRAMEWORK_VERSION,
        instance_count=training_instance_count,
        instance_type=training_instance_type,
        sagemaker_session=pipeline_session,
        hyperparameters={
            "num_epochs": training_hyperparameter_num_epochs,
            "batch_size": training_hyperparameter_batch_size,
            "learning_rate": training_hyperparameter_learning_rate,
        },
        source_dir=pipeline_steps_source_dir,
        entry_point="train.py",
    )
    train_args = estimator.fit(
        inputs={
            "train": TrainingInput(
                s3_data=step_process.properties.ProcessingOutputConfig.Outputs[  # pylint: disable=no-member
                    "train"
                ].S3Output.S3Uri,
                content_type="text/csv",
            ),
            "validation": TrainingInput(
                s3_data=step_process.properties.ProcessingOutputConfig.Outputs[  # pylint: disable=no-member
                    "validation"
                ].S3Output.S3Uri,
                content_type="text/csv",
            ),
        },
    )
    step_train = TrainingStep(
        name="Train", step_args=train_args, cache_config=cache_config
    )

    # evaluation step
    script_evaluation = FrameworkProcessor(
        estimator_cls=PyTorch,
        framework_version=PYTORCH_FRAMEWORK_VERSION,
        py_version=PYTHON_VERSION,
        instance_count=evaluation_instance_count,
        instance_type=evaluation_instance_type,
        sagemaker_session=pipeline_session,
        role=pipeline_role_arn,
    )
    evaluation_report = PropertyFile(
        name="EvaluationReport", output_name="evaluation", path="evaluation.json"
    )
    evaluation_args = script_evaluation.run(
        inputs=[
            ProcessingInput(
                source=step_train.properties.ModelArtifacts.S3ModelArtifacts,  # pylint: disable=no-member
                destination=f"{preprocessing_files_base_dir}/model",
            ),
            ProcessingInput(
                source=step_process.properties.ProcessingOutputConfig.Outputs[  # pylint: disable=no-member
                    "test"
                ].S3Output.S3Uri,
                destination=f"{preprocessing_files_base_dir}/test",
            ),
        ],
        outputs=[
            ProcessingOutput(
                output_name="evaluation",
                source=f"{preprocessing_files_base_dir}/evaluation",
            ),
        ],
        source_dir=pipeline_steps_source_dir,
        code="evaluate.py",
    )
    step_evaluation = ProcessingStep(
        name="Evaluate",
        step_args=evaluation_args,
        property_files=[evaluation_report],
        cache_config=cache_config,
    )
    model_metrics = ModelMetrics(
        model_statistics=MetricsSource(
            s3_uri="{}/evaluation.json".format(  # pylint: disable=consider-using-f-string
                step_evaluation.arguments["ProcessingOutputConfig"]["Outputs"][0][
                    "S3Output"
                ]["S3Uri"]
            ),
            content_type="application/json",
        )
    )

    # model register step
    model_package_group_name = f"{pipeline_name}-model-group"
    model = PyTorchModel(
        framework_version=PYTORCH_FRAMEWORK_VERSION,
        py_version=PYTHON_VERSION,
        model_data=step_train.properties.ModelArtifacts.S3ModelArtifacts,  # pylint: disable=no-member
        sagemaker_session=pipeline_session,
        role=pipeline_role_arn,
    )
    pipeline_model = PipelineModel(
        models=[model], role=pipeline_role_arn, sagemaker_session=pipeline_session
    )
    register_args = pipeline_model.register(
        content_types=["application/csv"],
        response_types=["application/csv"],
        inference_instances=[real_time_inference_instance_type],
        transform_instances=[batch_transform_inference_instance_type],
        model_package_group_name=model_package_group_name,
        approval_status="Approved",
        model_metrics=model_metrics,
    )
    step_register_model = ModelStep(
        name="CMS-PM",
        step_args=register_args,
    )

    # deploy model step
    deploy_model_step = LambdaStep(
        name="Deploy",
        lambda_func=Lambda(
            function_arn=deploy_model_function_arn,
        ),
        inputs={
            "ModelPackageGroupName": model_package_group_name,
            "EndpointName": endpoint_name,
            "InferenceInstanceCount": real_time_inference_instance_count,
            "InferenceInstanceType": real_time_inference_instance_type,
            "PipelineExecutionRoleArn": pipeline_role_arn,
            "ResourceNameSuffix": resource_name_suffix,
        },
        outputs=[],
    )

    # evaluation accuracy condition step
    model_accuracy_condition = ConditionGreaterThanOrEqualTo(
        left=JsonGet(
            step_name=step_evaluation.name,
            property_file=evaluation_report,
            json_path="binary_classification_metrics.accuracy.value",
        ),
        right=model_accuracy_threshold,
    )
    step_condition = ConditionStep(
        name="CheckModelAccuracy",
        conditions=[model_accuracy_condition],
        if_steps=[step_register_model, deploy_model_step],
        else_steps=[],
    )

    return Pipeline(
        name=pipeline_name,
        parameters=[
            raw_dataset_s3_uri,
            preprocessing_instance_type,
            preprocessing_instance_count,
            training_instance_type,
            training_instance_count,
            training_hyperparameter_num_epochs,
            training_hyperparameter_batch_size,
            training_hyperparameter_learning_rate,
            evaluation_instance_type,
            evaluation_instance_count,
            model_accuracy_threshold,
            real_time_inference_instance_type,
            real_time_inference_instance_count,
            batch_transform_inference_instance_type,
        ],
        steps=[step_process, step_train, step_evaluation, step_condition],
    )
