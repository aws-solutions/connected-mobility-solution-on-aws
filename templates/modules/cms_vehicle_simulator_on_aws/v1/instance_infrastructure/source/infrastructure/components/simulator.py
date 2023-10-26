# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

# Standard Library
from typing import TYPE_CHECKING, Any, Callable

# Third Party Libraries
from aws_cdk import (
    ArnFormat,
    Aws,
    Duration,
    Fn,
    RemovalPolicy,
    Stack,
    aws_dynamodb,
    aws_iam,
    aws_kms,
    aws_lambda,
    aws_logs,
    aws_s3,
    aws_ssm,
    aws_stepfunctions,
    aws_stepfunctions_tasks,
    custom_resources,
)
from constructs import Construct

# Connected Mobility Solution on AWS
from ...config.constants import VSConstants
from .. import generate_lambda_cloudwatch_logs_policy_document, generate_physical_name

if TYPE_CHECKING:
    # Connected Mobility Solution on AWS
    from ..cms_vehicle_simulator_on_aws_stack import InfrastructureSimulatorStack


def function_singleton(function: Any) -> Callable[[SimulatorConstruct], Any]:
    def wrapper(self: SimulatorConstruct) -> Any:
        if getattr(self, "_" + function.__name__, None):
            return getattr(self, "_" + function.__name__)
        new_obj = function(self)
        setattr(self, "_" + function.__name__, new_obj)
        return new_obj

    return wrapper


# pylint: disable=too-many-instance-attributes
class SimulatorConstruct(Construct):
    def __init__(self, scope: InfrastructureSimulatorStack, stack_id: str) -> None:
        super().__init__(scope, stack_id)

        self.devices_types_table_arn = aws_ssm.StringParameter.from_string_parameter_name(
            self,
            "ssm-devices-types-table-arn",
            f"/{VSConstants.STAGE}/{VSConstants.APP_NAME}/dynamodb/devices-types-table-arn",
        ).string_value
        self.simulations_table_arn = aws_ssm.StringParameter.from_string_parameter_name(
            self,
            "ssm-simulations-table-arn",
            f"/{VSConstants.STAGE}/{VSConstants.APP_NAME}/dynamodb/simulations-table-arn",
        ).string_value
        self.devices_types_table_name = aws_ssm.StringParameter.from_string_parameter_name(
            self,
            "ssm-devices-types-table-name",
            f"/{VSConstants.STAGE}/{VSConstants.APP_NAME}/dynamodb/devices-types-table-name",
        ).string_value
        self.simulations_table_name = aws_ssm.StringParameter.from_string_parameter_name(
            self,
            "ssm-simulations-table-name",
            f"/{VSConstants.STAGE}/{VSConstants.APP_NAME}/dynamodb/simulations-table-name",
        ).string_value

        routes_bucket = aws_s3.Bucket.from_bucket_arn(
            self,
            "routes-bucket",
            Fn.import_value(f"{VSConstants.APP_NAME}-routes-bucket-arn"),
        )

        simulator_lambda_name = f"{VSConstants.APP_NAME}-simulator-lambda"
        provisioning_lambda_name = f"{VSConstants.APP_NAME}-provisioning-lambda"
        cleanup_lambda_name = f"{VSConstants.APP_NAME}-cleanup-lambda"

        simulator_lambda_role = aws_iam.Role(
            self,
            "simulator-engine-lambda-role",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            path="/",
            inline_policies={
                "s3-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=["s3:GetObject"],
                            resources=[f"{routes_bucket.bucket_arn}/*"],
                        )
                    ]
                ),
                "dynamodb-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=["dynamodb:GetItem"],
                            resources=[self.simulations_table_arn],
                        )
                    ]
                ),
                "iot-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=["iot:Publish"],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="iot",
                                    resource="topic",
                                    resource_name=f"{VSConstants.TOPIC_PREFIX}/*",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                            ],
                        ),
                    ]
                ),
                "cloudwatch-logs-policy": generate_lambda_cloudwatch_logs_policy_document(
                    self, simulator_lambda_name
                ),
            },
        )

        provisioning_lambda_role = aws_iam.Role(
            self,
            "provisioning-lambda-role",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            path="/",
            inline_policies={
                "iot-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "iot:CreateKeysAndCertificate",
                                "iot:AttachThingPrincipal",
                            ],
                            resources=["*"],
                        ),
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=["iot:CreateThing", "iot:DescribeThing"],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="iot",
                                    resource="thing",
                                    resource_name="*",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                            ],
                        ),
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=["iot:AddThingToThingGroup"],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="iot",
                                    resource="thing",
                                    resource_name="*",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                                Stack.of(self).format_arn(
                                    service="iot",
                                    resource="thinggroup",
                                    resource_name="*",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                            ],
                        ),
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=["iot:CreatePolicy"],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="iot",
                                    resource="policy",
                                    resource_name="*",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                            ],
                        ),
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=["iot:AttachPolicy"],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="iot",
                                    resource="cert",
                                    resource_name="*",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                            ],
                        ),
                    ]
                ),
                "secrets-manager-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "secretsmanager:CreateSecret",
                                "secretsmanager:TagResource",
                            ],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="secretsmanager",
                                    resource="secret",
                                    resource_name="*",
                                    arn_format=ArnFormat.COLON_RESOURCE_NAME,
                                ),
                            ],
                        )
                    ]
                ),
                "cloudwatch-logs-policy": generate_lambda_cloudwatch_logs_policy_document(
                    self, provisioning_lambda_name
                ),
            },
        )

        cleanup_lambda_role = aws_iam.Role(
            self,
            "cleanup-lambda-role",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            path="/",
            inline_policies={
                "iot-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=["iot:DeleteThing"],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="iot",
                                    resource="thing",
                                    resource_name="*",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                            ],
                        ),
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=["iot:DeletePolicy"],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="iot",
                                    resource="policy",
                                    resource_name="*",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                            ],
                        ),
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=["iot:DeleteCertificate", "iot:DetachPolicy"],
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
                                "iot:DetachThingPrincipal",
                                "iot:ListThings",
                                "iot:ListThingPrincipals",
                                "iot:ListPrincipalPolicies",
                            ],
                            resources=["*"],
                        ),
                    ]
                ),
                "secrets-manager-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=["secretsmanager:DeleteSecret"],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="secretsmanager",
                                    resource="secret",
                                    resource_name="vs-device/*",
                                    arn_format=ArnFormat.COLON_RESOURCE_NAME,
                                ),
                            ],
                        )
                    ]
                ),
                "tagging-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=["tag:GetResources"],
                            resources=["*"],
                        )
                    ]
                ),
                "cloudwatch-logs-policy": generate_lambda_cloudwatch_logs_policy_document(
                    self, cleanup_lambda_name
                ),
            },
        )

        iot_endpoint_custom_resource = custom_resources.AwsCustomResource(
            self,
            "iot-endpoint-custom-resource",
            on_create=custom_resources.AwsSdkCall(
                service="Iot",
                action="describeEndpoint",
                physical_resource_id=custom_resources.PhysicalResourceId.from_response(
                    "endpointAddress"
                ),
                parameters={"endpointType": "iot:Data-ATS"},
            ),
            policy=custom_resources.AwsCustomResourcePolicy.from_sdk_calls(
                resources=custom_resources.AwsCustomResourcePolicy.ANY_RESOURCE
            ),
            install_latest_aws_sdk=False,
        )

        iot_endpoint = iot_endpoint_custom_resource.get_response_field(
            "endpointAddress"
        )

        solution_id = aws_ssm.StringParameter.from_string_parameter_name(
            self,
            "ssm-solution-id",
            f"/{VSConstants.STAGE}/{VSConstants.APP_NAME}/solution/id",
        ).string_value

        dependency_layer = aws_lambda.LayerVersion.from_layer_version_arn(
            self,
            "simulator-device-layer-version",
            aws_ssm.StringParameter.from_string_parameter_name(
                self,
                "ssm-simulator-dependency-layer-arn",
                f"/{VSConstants.STAGE}/{VSConstants.APP_NAME}/arns/dependency-layer-arn",
            ).string_value,
        )

        self.provisioning_lambda_function = aws_lambda.Function(
            self,
            "provisioning-lambda",
            function_name=provisioning_lambda_name,
            code=aws_lambda.Code.from_asset("source/handlers"),
            description="CMS Vehicle Simulator Provisioning Function",
            environment={
                "IOT_ENDPOINT": iot_endpoint,
                "SEND_ANONYMOUS_METRIC": Fn.import_value(
                    f"{VSConstants.APP_NAME}-send-anonymous-usage"
                ),
                "SOLUTION_ID": solution_id,
                "VERSION": Fn.import_value(f"{VSConstants.APP_NAME}-solution-version"),
                "SIMULATOR_THING_GROUP_NAME": Fn.import_value(
                    f"{VSConstants.APP_NAME}-thing-group-name"
                ),
                "TOPIC_PREFIX": VSConstants.TOPIC_PREFIX,
                "USER_AGENT_STRING": VSConstants.USER_AGENT_STRING,
            },
            handler="stepfunction.handlers.provision_handler",
            runtime=aws_lambda.Runtime.PYTHON_3_10,
            timeout=Duration.minutes(1),
            role=provisioning_lambda_role,
            layers=[dependency_layer],
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
        )

        self.simulator_lambda_function = aws_lambda.Function(
            self,
            "simulator-engine-lambda",
            function_name=simulator_lambda_name,
            code=aws_lambda.Code.from_asset("source/handlers"),
            description="CMS Vehicle Simulator Function",
            environment={
                "IOT_ENDPOINT": iot_endpoint,
                "SEND_ANONYMOUS_METRIC": Fn.import_value(
                    f"{VSConstants.APP_NAME}-send-anonymous-usage"
                ),
                "SOLUTION_ID": solution_id,
                "VERSION": Fn.import_value(f"{VSConstants.APP_NAME}-solution-version"),
                "ROUTE_BUCKET": routes_bucket.bucket_name,
                "SIM_TABLE": self.simulations_table_name,
                "TOPIC_PREFIX": f"{VSConstants.TOPIC_PREFIX}",
                "USER_AGENT_STRING": VSConstants.USER_AGENT_STRING,
            },
            handler="stepfunction.handlers.data_sim_handler",
            runtime=aws_lambda.Runtime.PYTHON_3_10,
            timeout=Duration.minutes(1),
            role=simulator_lambda_role,
            layers=[dependency_layer],
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
        )

        self.cleanup_lambda_function = aws_lambda.Function(
            self,
            "cleanup-lambda",
            function_name=cleanup_lambda_name,
            code=aws_lambda.Code.from_asset("source/handlers"),
            description="Provisioning Artifact Cleanup Function",
            environment={
                "IOT_ENDPOINT": iot_endpoint,
                "SEND_ANONYMOUS_METRIC": Fn.import_value(
                    f"{VSConstants.APP_NAME}-send-anonymous-usage"
                ),
                "SOLUTION_ID": solution_id,
                "VERSION": Fn.import_value(f"{VSConstants.APP_NAME}-solution-version"),
                "SIMULATOR_THING_GROUP_NAME": Fn.import_value(
                    f"{VSConstants.APP_NAME}-thing-group-name"
                ),
                "USER_AGENT_STRING": VSConstants.USER_AGENT_STRING,
            },
            handler="stepfunction.handlers.cleanup_handler",
            runtime=aws_lambda.Runtime.PYTHON_3_10,
            timeout=Duration.minutes(1),
            role=cleanup_lambda_role,
            layers=[dependency_layer],
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
        )

        self.done = aws_stepfunctions.Succeed(self, "Done")

        self.setup_step_function()

        self.ssm_outputs()

        scope.export_value(iot_endpoint, name=f"{VSConstants.APP_NAME}-iot-end-point")

    def ssm_outputs(self) -> None:
        aws_ssm.StringParameter(
            self,
            "simulator-state-machine",
            string_value=self.simulator_state_machine.state_machine_name,
            description="State machine name",
            parameter_name=f"/{VSConstants.STAGE}/{VSConstants.APP_NAME}/names/simulator-state-machine-name",
        )
        aws_ssm.StringParameter(
            self,
            "simulator-state-machine-arn",
            string_value=self.simulator_state_machine.state_machine_arn,
            description="State machine arn",
            parameter_name=f"/{VSConstants.STAGE}/{VSConstants.APP_NAME}/arns/simulator-state-machine-arn",
        )

    def setup_step_function(self) -> None:
        definition = aws_stepfunctions.Chain.start(
            self.get_device_type_map().iterator(
                self.get_device_type_info().next(
                    self.devices_pass().next(
                        self.devices_map()
                        .iterator(
                            self.provisioning_invoke()
                            .add_catch(self.done)
                            .next(
                                self.simulator_invoke()
                                .add_catch(
                                    self.update_sim_table(), result_path="$.error"
                                )
                                .next(
                                    aws_stepfunctions.Choice(
                                        self,
                                        "engine-choice",
                                    )
                                    .when(
                                        aws_stepfunctions.Condition.number_greater_than_json_path(
                                            "$.simulation.duration",
                                            "$.options.runtime",
                                        ),
                                        aws_stepfunctions.Wait(
                                            self,
                                            "engine-wait",
                                            time=aws_stepfunctions.WaitTime.seconds_path(
                                                "$.simulation.interval"
                                            ),
                                        ).next(self.simulator_invoke()),
                                    )
                                    .otherwise(
                                        aws_stepfunctions.Choice(
                                            self, "devicesRunning?"
                                        )
                                        .when(
                                            aws_stepfunctions.Condition.boolean_equals(
                                                "$.options.restart", True
                                            ),
                                            self.simulator_invoke(),
                                        )
                                        .otherwise(
                                            self.update_sim_table().next(self.done)
                                        )
                                    )
                                )
                            )
                        )
                        .add_catch(self.cleanup_invoke())
                        .next(self.cleanup_invoke())
                    )
                )
            )
        )

        simulator_log_group_kms_key = aws_kms.Key(
            self,
            "vs-simulator-log-group-kms-key",
            alias="vs-simulator-log-group-kms-key",
            enable_key_rotation=True,
        )

        simulator_log_group = aws_logs.LogGroup(
            self,
            "step-functions-log-group",
            removal_policy=RemovalPolicy.RETAIN,
            retention=aws_logs.RetentionDays.THREE_MONTHS,
            encryption_key=simulator_log_group_kms_key,
            log_group_name=generate_physical_name(
                scope=self,
                prefix="/aws/vendedlogs/states",
                physical_name_substrings=[
                    Stack.of(self).stack_name,
                    self.node.scope.node.id,  # type: ignore
                    "state-machine-log",
                ],
                max_length=512,
            ),
        )

        simulator_log_group_kms_key.add_to_resource_policy(
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

        simulator_state_machine_role = aws_iam.Role(
            self,
            "simulator-statemachine-role",
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
                                self.simulator_lambda_function.function_arn,
                                self.provisioning_lambda_function.function_arn,
                                self.cleanup_lambda_function.function_arn,
                            ],
                        )
                    ]
                ),
                "sim-table-dynamodb-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            actions=["dynamodb:UpdateItem"],
                            effect=aws_iam.Effect.ALLOW,
                            resources=[
                                Stack.of(self).format_arn(
                                    service="dynamodb",
                                    resource="table",
                                    resource_name=f"{self.simulations_table_name}",
                                )
                            ],
                        )
                    ]
                ),
                "device-types-table-dynamodb-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            actions=["dynamodb:GetItem"],
                            effect=aws_iam.Effect.ALLOW,
                            resources=[
                                Stack.of(self).format_arn(
                                    service="dynamodb",
                                    resource="table",
                                    resource_name=f"{self.devices_types_table_name}",
                                )
                            ],
                        )
                    ]
                ),
            },
        )

        self.simulator_state_machine = aws_stepfunctions.StateMachine(
            self,
            "step-functions",
            definition=definition,
            role=simulator_state_machine_role,
            logs=aws_stepfunctions.LogOptions(
                destination=simulator_log_group,
                level=aws_stepfunctions.LogLevel.ALL,
                include_execution_data=False,
            ),
            tracing_enabled=True,
        )

        simulator_state_machine_role.node.try_remove_child("DefaultPolicy")

    # ----------------------------------- Step Functions Pieces -----------------------------------
    @function_singleton
    def get_device_type_map(self) -> aws_stepfunctions.Map:
        return aws_stepfunctions.Map(
            self,
            "get-device-type-map",
            items_path="$.simulation.devices",
            parameters={
                "type_id.$": "$$.Map.Item.Value.type_id",
                "amount.$": "States.StringToJson($$.Map.Item.Value.amount)",
                "simulation.$": "$.simulation",
            },
            max_concurrency=0,
        )

    @function_singleton
    def provisioning_invoke(self) -> aws_stepfunctions_tasks.LambdaInvoke:
        return aws_stepfunctions_tasks.LambdaInvoke(
            self,
            "provisioning-invoke",
            lambda_function=self.provisioning_lambda_function,
            retry_on_service_exceptions=True,
            result_path=aws_stepfunctions.JsonPath.DISCARD,
            payload_response_only=True,
        )

    @function_singleton
    def simulator_invoke(self) -> aws_stepfunctions_tasks.LambdaInvoke:
        return aws_stepfunctions_tasks.LambdaInvoke(
            self,
            "simulator-invoke",
            lambda_function=self.simulator_lambda_function,
            retry_on_service_exceptions=True,
            result_path="$.options",
            payload_response_only=True,
        )

    @function_singleton
    def cleanup_invoke(self) -> aws_stepfunctions_tasks.LambdaInvoke:
        return aws_stepfunctions_tasks.LambdaInvoke(
            self,
            "cleanup-invoke",
            lambda_function=self.cleanup_lambda_function,
            retry_on_service_exceptions=True,
            result_path=aws_stepfunctions.JsonPath.DISCARD,
        )

    @function_singleton
    def update_sim_table(self) -> aws_stepfunctions_tasks.DynamoUpdateItem:
        update_sim_table = aws_stepfunctions_tasks.DynamoUpdateItem(
            self,
            "update-sim-table",
            table=aws_dynamodb.Table.from_table_arn(
                self, "simulations-table", self.simulations_table_arn
            ),
            key={
                "sim_id": aws_stepfunctions_tasks.DynamoAttributeValue.from_string(
                    aws_stepfunctions.JsonPath.string_at("$.simulation.sim_id")
                )
            },
            update_expression="SET stage = :stage, updatedAt = :time",
            expression_attribute_values={
                ":stage": aws_stepfunctions_tasks.DynamoAttributeValue.from_string(
                    "sleeping"
                ),
                ":time": aws_stepfunctions_tasks.DynamoAttributeValue.from_string(
                    aws_stepfunctions.JsonPath.string_at("$$.State.EnteredTime")
                ),
            },
            condition_expression="attribute_exists(sim_id)",
        )

        update_sim_table.add_catch(
            self.done, errors=["DynamoDB.ConditionalCheckFailedException"]
        )

        return update_sim_table

    def devices_map(self) -> aws_stepfunctions.Map:
        return aws_stepfunctions.Map(
            self,
            "device-map",
            items_path="$.amount_range",
            parameters={
                "simulation.$": "$.simulation",
                "info.$": "$.info",
                "index.$": "$$.Map.Item.Index",
            },
            max_concurrency=0,
            result_path=aws_stepfunctions.JsonPath.DISCARD,
        )

    def devices_pass(self) -> aws_stepfunctions.Pass:
        return aws_stepfunctions.Pass(
            self,
            "device-pass",
            parameters={
                "amount_range.$": "States.ArrayRange(1,$.amount,1)",
                "info.$": "$.info",
                "simulation.$": "$.simulation",
            },
        )

    def get_device_type_info(self) -> aws_stepfunctions_tasks.DynamoGetItem:
        return aws_stepfunctions_tasks.DynamoGetItem(
            self,
            "get-device-type-info",
            table=aws_dynamodb.Table.from_table_arn(
                self, "device-types-table", self.devices_types_table_arn
            ),
            key={
                "type_id": aws_stepfunctions_tasks.DynamoAttributeValue.from_string(
                    aws_stepfunctions.JsonPath.string_at("$.type_id")
                )
            },
            result_selector={
                "name.$": "$.Item.name",
                "topic.$": "$.Item.topic",
                "payload.$": "$.Item.payload",
                "simulation": "$.simulation",
                "amount": "$.amount",
            },
            result_path="$.info",
        )
