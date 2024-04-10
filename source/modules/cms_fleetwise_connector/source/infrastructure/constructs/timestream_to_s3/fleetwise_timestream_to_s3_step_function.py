# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

# Standard Library
from typing import Any, Dict

# AWS Libraries
from aws_cdk import (
    ArnFormat,
    Aws,
    Duration,
    Fn,
    RemovalPolicy,
    Stack,
    aws_events,
    aws_events_targets,
    aws_iam,
    aws_kms,
    aws_lambda,
    aws_logs,
    aws_stepfunctions,
    aws_stepfunctions_tasks,
)
from constructs import Construct

# CMS Common Library
from cms_common.config.metrics import OperationalMetricsInput
from cms_common.config.resource_names import ResourceName, ResourcePrefix
from cms_common.config.stack_inputs import SolutionConfigInputs
from cms_common.constructs.vpc_construct import VpcConstruct

# Connected Mobility Solution on AWS
from ..module_integration import (
    ModuleConfigInputs,
    TelemetryBucketInputs,
    TimestreamOutputs,
)
from .fleetwise_timestream_query_vin_task import FleetWiseTimestreamQueryVin
from .fleetwise_timestream_time_range_handler_task import (
    FleetWiseTimestreamTimeRangeHandler,
)
from .fleetwise_timestream_unload_to_s3_task import FleetWiseTimestreamUnloadToS3


class FleetWiseTimestreamToS3Construct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        solution_config_inputs: SolutionConfigInputs,
        module_config: ModuleConfigInputs,
        timestream: TimestreamOutputs,
        telemetry_bucket: TelemetryBucketInputs,
        operational_metrics: OperationalMetricsInput,
        dependency_layer: aws_lambda.LayerVersion,
        vpc_construct: VpcConstruct,
    ) -> None:
        super().__init__(scope, construct_id)

        timestream_time_range_lambda_function = (
            FleetWiseTimestreamTimeRangeHandler.create_lambda(
                self,
                solution_config_inputs=solution_config_inputs,
                module_config=module_config,
                operational_metrics=operational_metrics,
                dependency_layer=dependency_layer,
                vpc_construct=vpc_construct,
            )
        )

        timestream_query_vins_lambda_function = (
            FleetWiseTimestreamQueryVin.create_lambda(
                self,
                app_unique_id=module_config.app_unique_id,
                solution_config_inputs=solution_config_inputs,
                timestream=timestream,
                operational_metrics=operational_metrics,
                vpc_construct=vpc_construct,
            )
        )

        timestream_unload_to_s3_lambda_function = FleetWiseTimestreamUnloadToS3.create_lambda(
            self,
            app_unique_id=module_config.app_unique_id,
            solution_config_inputs=solution_config_inputs,
            timestream=timestream,
            telemetry_bucket=telemetry_bucket,
            operational_metrics=operational_metrics,
            timestream_unload_s3_prefix_path=module_config.timestream_unload_s3_prefix_path,
            vpc_construct=vpc_construct,
        )

        timestream_to_s3_step_function = self.create_step_function(
            solution_config_inputs=solution_config_inputs,
            module_config=module_config,
            timestream=timestream,
            telemetry_bucket=telemetry_bucket,
            timestream_time_range_lambda_function=timestream_time_range_lambda_function,
            timestream_query_vins_lambda_function=timestream_query_vins_lambda_function,
            timestream_unload_to_s3_lambda_function=timestream_unload_to_s3_lambda_function,
        )

        step_function_cron_rule = aws_events.Rule(
            self,
            "cms-fleetwise-step-function-cron-rule",
            schedule=aws_events.Schedule.rate(
                duration=Duration.minutes(
                    module_config.timestream_to_s3_unload_interval_minutes
                )
            ),
        )

        step_function_cron_rule.add_target(
            aws_events_targets.SfnStateMachine(timestream_to_s3_step_function)
        )

    # pylint: disable=R0914
    def create_step_function(
        self,
        solution_config_inputs: SolutionConfigInputs,
        module_config: ModuleConfigInputs,
        timestream: TimestreamOutputs,
        telemetry_bucket: TelemetryBucketInputs,
        timestream_time_range_lambda_function: aws_lambda.Function,
        timestream_query_vins_lambda_function: aws_lambda.Function,
        timestream_unload_to_s3_lambda_function: aws_lambda.Function,
    ) -> Any:

        timestream_get_time_range_lambda_task = aws_stepfunctions_tasks.LambdaInvoke(
            self,
            "timestream-get-unload-time-range-lambda-task",
            state_name="Generate Unload Query Time Range",
            lambda_function=timestream_time_range_lambda_function,
            payload=aws_stepfunctions.TaskInput.from_object(
                {
                    "requestType": FleetWiseTimestreamTimeRangeHandler.RequestType.GET.value,
                }
            ),
            result_selector={
                "timeInfo.$": "$.Payload",
            },
            retry_on_service_exceptions=True,
        )

        timestream_query_vins_lambda_task = aws_stepfunctions_tasks.LambdaInvoke(
            self,
            "timestream-query-vins-lambda-task",
            state_name="Get Batches of Available VINs in Time Range",
            lambda_function=timestream_query_vins_lambda_function,
            result_path="$.getVinsResult",
            payload=aws_stepfunctions.TaskInput.from_object(
                {
                    "timestream": _generate_timestream_parameter(timestream),
                    "cmsConnectStore": _generate_cms_connect_store_parameter(
                        telemetry_bucket, module_config.timestream_unload_s3_prefix_path
                    ),
                    "timeInfo.$": "$.timeInfo",
                }
            ),
            result_selector={
                "vinBatches.$": "$.Payload.vin_batches",
            },
            retry_on_service_exceptions=True,
        )

        get_data_per_batch_of_vins_map = aws_stepfunctions.Map(
            self,
            "get-data-per-batch-of-vins-map",
            state_name="Process Each VIN Batch",
            max_concurrency=1,
            items_path="$.getVinsResult.vinBatches",
            result_path="$.vin_batch",
            parameters={
                "vinBatch.$": "$$.Map.Item.Value",
                "timestream": _generate_timestream_parameter(timestream),
                "cmsConnectStore": _generate_cms_connect_store_parameter(
                    telemetry_bucket, module_config.timestream_unload_s3_prefix_path
                ),
                "fleetwise": _generate_fleetwise_config_parameter(module_config),
                "timeInfo.$": "$.timeInfo",
            },
        )

        timestream_unload_to_s3_lambda_task = aws_stepfunctions_tasks.LambdaInvoke(
            self,
            "timestream-unload-to-s3-lambda-task",
            state_name="Unload Data to S3 Per Batch of VINs",
            lambda_function=timestream_unload_to_s3_lambda_function,
            output_path="$.Payload",
            retry_on_service_exceptions=True,
        )

        get_data_per_batch_of_vins_map.item_processor(
            processor=timestream_unload_to_s3_lambda_task,
            mode=aws_stepfunctions.ProcessorMode.DISTRIBUTED,
            execution_type=aws_stepfunctions.ProcessorType.STANDARD,
        )

        timestream_set_end_time_lambda_task = aws_stepfunctions_tasks.LambdaInvoke(
            self,
            "timestream-set-unload-end-time-lambda-task",
            state_name="Update Last Unload Query End Time",
            lambda_function=timestream_time_range_lambda_function,
            result_path="$.timeInfo",
            payload=aws_stepfunctions.TaskInput.from_object(
                {
                    "requestType": FleetWiseTimestreamTimeRangeHandler.RequestType.SET.value,
                    "timeInfo.$": "$.timeInfo",
                }
            ),
            retry_on_service_exceptions=True,
        )

        check_for_available_data_choice = (
            aws_stepfunctions.Choice(
                self,
                "check-for-data-existence-in-query-range",
                state_name="Check for Existence of Data in Query Range",
            )
            .when(
                aws_stepfunctions.Condition.is_not_present(
                    "$.getVinsResult.vinBatches[0][0]"
                ),
                aws_stepfunctions.Succeed(
                    self, "skip-no-data", state_name="Skipping Unload: No New Data"
                ),
            )
            .otherwise(get_data_per_batch_of_vins_map)
            .afterwards()
        )

        step_function_chain = (
            aws_stepfunctions.Chain.start(timestream_get_time_range_lambda_task)
            .next(timestream_query_vins_lambda_task)
            .next(check_for_available_data_choice)
            .next(timestream_set_end_time_lambda_task)
        )

        step_function_definition = aws_stepfunctions.DefinitionBody.from_chainable(
            step_function_chain
        )

        log_group_kms_key = aws_kms.Key(
            self,
            "log-group-kms-key",
            enable_key_rotation=True,
        )

        unique_stack_id_part = Fn.select(2, Fn.split("/", Aws.STACK_ID))
        log_group = aws_logs.LogGroup(
            self,
            "step-functions-log-group",
            removal_policy=RemovalPolicy.RETAIN,
            retention=aws_logs.RetentionDays.THREE_MONTHS,
            encryption_key=log_group_kms_key,
            log_group_name=f"/aws/vendedlogs/{module_config.app_unique_id}/{solution_config_inputs.module_short_name}/step-function-{unique_stack_id_part}",
        )

        log_group_kms_key.add_to_resource_policy(
            statement=aws_iam.PolicyStatement(
                effect=aws_iam.Effect.ALLOW,
                principals=[
                    aws_iam.ServicePrincipal(
                        f"logs.{Stack.of(self).region}.amazonaws.com"
                    )
                ],
                actions=["kms:Encrypt", "kms:Decrypt", "kms:GenerateDataKey"],
                resources=["*"],
            )
        )

        state_machine_name = ResourceName.hyphen_separated(
            prefix=ResourcePrefix.hyphen_separated(
                app_unique_id=module_config.app_unique_id,
                module_name=solution_config_inputs.module_short_name,
            ),
            name="timestream-to-s3",
        )

        step_function_role = aws_iam.Role(
            self,
            "state-machine-role",
            assumed_by=aws_iam.ServicePrincipal("states.amazonaws.com"),
            path="/",
            inline_policies={
                "cloudwatch-logs-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            actions=[
                                "logs:CreateLogDelivery",
                                "logs:GetLogDelivery",
                                "logs:UpdateLogDelivery",
                                "logs:DeleteLogDelivery",
                                "logs:ListLogDeliveries",
                            ],
                            effect=aws_iam.Effect.ALLOW,
                            resources=["*"],
                        )
                    ]
                ),
                "cloudwatch-logs-policy2": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            actions=[
                                "logs:PutResourcePolicy",
                                "logs:DescribeResourcePolicies",
                                "logs:DescribeLogGroups",
                            ],
                            effect=aws_iam.Effect.ALLOW,
                            resources=[
                                Stack.of(self).format_arn(
                                    resource="*",
                                    partition=Aws.PARTITION,
                                    region=Stack.of(self).region,
                                    service="logs",
                                    account=Stack.of(self).account,
                                    arn_format=ArnFormat.COLON_RESOURCE_NAME,
                                )
                            ],
                        )
                    ]
                ),
                "xray-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            actions=[
                                "xray:GetSamplingRules",
                                "xray:GetSamplingTargets",
                                "xray:PutTelemetryRecords",
                                "xray:PutTraceSegments",
                            ],
                            effect=aws_iam.Effect.ALLOW,
                            resources=["*"],
                        )
                    ]
                ),
                "lambda-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            actions=["Lambda:InvokeFunction"],
                            effect=aws_iam.Effect.ALLOW,
                            resources=[
                                timestream_query_vins_lambda_function.function_arn,
                                timestream_unload_to_s3_lambda_function.function_arn,
                                timestream_time_range_lambda_function.function_arn,
                            ],
                        )
                    ]
                ),
                "step-function-execution-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            actions=["states:StartExecution"],
                            effect=aws_iam.Effect.ALLOW,
                            resources=[
                                Stack.of(self).format_arn(
                                    resource_name=state_machine_name,
                                    resource="stateMachine",
                                    partition=Aws.PARTITION,
                                    region=Stack.of(self).region,
                                    service="states",
                                    account=Stack.of(self).account,
                                    arn_format=ArnFormat.COLON_RESOURCE_NAME,
                                )
                            ],
                        )
                    ]
                ),
            },
        )

        state_machine = aws_stepfunctions.StateMachine(
            self,
            "step-function-state-machine",
            state_machine_name=state_machine_name,
            definition_body=step_function_definition,
            role=step_function_role,
            logs=aws_stepfunctions.LogOptions(
                destination=log_group,
                level=aws_stepfunctions.LogLevel.ALL,
                include_execution_data=False,
            ),
            tracing_enabled=True,
            removal_policy=RemovalPolicy.DESTROY,
        )

        step_function_role.node.try_remove_child("DefaultPolicy")

        return state_machine


def _generate_timestream_parameter(timestream: TimestreamOutputs) -> Dict[str, str]:
    return {
        "databaseName": timestream.database_name,
        "tableName": timestream.table_name,
    }


def _generate_cms_connect_store_parameter(
    telemetry_bucket: TelemetryBucketInputs, telemetry_prefix_path: str
) -> Dict[str, str]:
    return {
        "telemetryBucketName": telemetry_bucket.bucket_name,
        "telemetryPrefixPath": f"{telemetry_prefix_path}/",
        "telemetryBucketKmsKeyArn": telemetry_bucket.bucket_key_arn,
    }


def _generate_fleetwise_config_parameter(
    module_config: ModuleConfigInputs,
) -> Dict[str, str]:
    return {
        "vehicleVinAttributeName": module_config.fleetwise_vehicle_vin_attribute_name
    }
