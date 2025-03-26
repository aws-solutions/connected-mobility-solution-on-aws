# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

# Standard Library
from typing import Any, Callable

# AWS Libraries
from aws_cdk import (
    ArnFormat,
    Aws,
    CustomResource,
    Duration,
    RemovalPolicy,
    Stack,
    aws_dynamodb,
    aws_ec2,
    aws_iam,
    aws_lambda,
    aws_logs,
    aws_s3,
    aws_stepfunctions,
    aws_stepfunctions_tasks,
    custom_resources,
)
from constructs import Construct

# CMS Common Library
from cms_common.config.resource_names import ResourceName, ResourcePrefix
from cms_common.config.stack_inputs import SolutionConfigInputs
from cms_common.constructs.custom_resource_lambda import CustomResourceLambdaConstruct
from cms_common.constructs.vpc_construct import VpcConstruct
from cms_common.policy_generators.ec2_vpc import generate_ec2_vpc_policy

# Connected Mobility Solution on AWS
from .. import generate_lambda_cloudwatch_logs_policy_document, generate_physical_name
from .storage import StorageConstruct


def function_singleton(function: Any) -> Callable[[SimulatorConstruct], Any]:
    def wrapper(self: SimulatorConstruct) -> Any:
        if getattr(self, "_" + function.__name__, None):
            return getattr(self, "_" + function.__name__)
        new_obj = function(self)
        setattr(self, "_" + function.__name__, new_obj)
        return new_obj

    return wrapper


class SimulatorConstruct(Construct):  # pylint: disable=too-many-instance-attributes
    def __init__(
        self,
        scope: Construct,
        stack_id: str,
        app_unique_id: str,
        solution_config_inputs: SolutionConfigInputs,
        storage_construct: StorageConstruct,
        custom_resource_lambda_construct: CustomResourceLambdaConstruct,
        routes_bucket_arn: str,
        dependency_layer: aws_lambda.LayerVersion,
        iot_topic_prefix: str,
        vpc_construct: VpcConstruct,
    ) -> None:
        super().__init__(scope, stack_id)

        self.devices_types_table_arn = storage_construct.devices_types_table.table_arn
        self.simulations_table_arn = storage_construct.simulations_table.table_arn
        self.devices_types_table_name = storage_construct.devices_types_table.table_name
        self.simulations_table_name = storage_construct.simulations_table.table_name

        simulator_custom_resource_policy = aws_iam.Policy(
            self,
            "custom-resource-policy",
            statements=[
                aws_iam.PolicyStatement(
                    effect=aws_iam.Effect.ALLOW,
                    actions=[
                        "iot:CreateThingGroup",
                        "iot:TagResource",
                    ],
                    resources=["*"],  # NOSONAR
                    # This action requires a wildcard resource
                ),
            ],
        )
        custom_resource_lambda_construct.add_policy_to_custom_resource_lambda(
            policy=simulator_custom_resource_policy
        )

        simulator_thing_group_custom_resource = CustomResource(
            self,
            "simulator-thing-group",
            service_token=custom_resource_lambda_construct.function.function_arn,
            resource_type="Custom::CreateIoTThingGroup",
            properties={
                "Resource": "CreateIoTThingGroup",
                "ThingGroupName": "cms-simulated-vehicle",
            },
        )
        simulator_thing_group_custom_resource.node.add_dependency(
            simulator_custom_resource_policy
        )

        routes_bucket = aws_s3.Bucket.from_bucket_arn(
            self,
            "routes-bucket",
            routes_bucket_arn,
        )

        simulator_lambda_name = ResourceName.hyphen_separated(
            prefix=ResourcePrefix.hyphen_separated(
                app_unique_id=app_unique_id,
                module_name=solution_config_inputs.module_short_name,
            ),
            name="simulator",
        )
        provisioning_lambda_name = ResourceName.hyphen_separated(
            prefix=ResourcePrefix.hyphen_separated(
                app_unique_id=app_unique_id,
                module_name=solution_config_inputs.module_short_name,
            ),
            name="provisioning",
        )
        cleanup_lambda_name = ResourceName.hyphen_separated(
            prefix=ResourcePrefix.hyphen_separated(
                app_unique_id=app_unique_id,
                module_name=solution_config_inputs.module_short_name,
            ),
            name="cleanup",
        )

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
                                    resource_name=f"{iot_topic_prefix}/*",
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                            ],
                        ),
                    ]
                ),
                "cloudwatch-logs-policy": generate_lambda_cloudwatch_logs_policy_document(
                    self, simulator_lambda_name
                ),
                "ec2-vpc-policy": generate_ec2_vpc_policy(
                    self,
                    vpc_construct=vpc_construct,
                    subnet_selection=vpc_construct.private_subnet_selection,
                    authorized_service="lambda.amazonaws.com",
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
                "ec2-vpc-policy": generate_ec2_vpc_policy(
                    self,
                    vpc_construct=vpc_construct,
                    subnet_selection=vpc_construct.private_subnet_selection,
                    authorized_service="lambda.amazonaws.com",
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
                "ec2-vpc-policy": generate_ec2_vpc_policy(
                    self,
                    vpc_construct=vpc_construct,
                    subnet_selection=vpc_construct.private_subnet_selection,
                    authorized_service="lambda.amazonaws.com",
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
            vpc=vpc_construct.vpc,
            vpc_subnets=vpc_construct.private_subnet_selection,
        )

        self.iot_endpoint = iot_endpoint_custom_resource.get_response_field(
            "endpointAddress"
        )

        self.provisioning_lambda_function = aws_lambda.Function(
            self,
            "provisioning-lambda",
            function_name=provisioning_lambda_name,
            code=aws_lambda.Code.from_asset("deployment/dist/lambda/stepfunction.zip"),
            description="CMS Vehicle Simulator Provisioning Function",
            environment={
                "IOT_ENDPOINT": self.iot_endpoint,
                "SOLUTION_ID": solution_config_inputs.solution_id,
                "VERSION": solution_config_inputs.solution_version,
                "SIMULATOR_THING_GROUP_NAME": simulator_thing_group_custom_resource.get_att(
                    "THING_GROUP_NAME"
                ).to_string(),
                "TOPIC_PREFIX": iot_topic_prefix,
                "USER_AGENT_STRING": solution_config_inputs.get_user_agent_string(),
            },
            handler="function.handlers.provision_handler",
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            timeout=Duration.minutes(1),
            role=provisioning_lambda_role,
            layers=[dependency_layer],
            vpc=vpc_construct.vpc,
            vpc_subnets=vpc_construct.private_subnet_selection,
            security_groups=[
                aws_ec2.SecurityGroup(
                    self,
                    "security-group-1",
                    vpc=vpc_construct.vpc,
                    allow_all_outbound=True,  # NOSONAR
                )
            ],
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
        )

        self.simulator_lambda_function = aws_lambda.Function(
            self,
            "simulator-engine-lambda",
            function_name=simulator_lambda_name,
            code=aws_lambda.Code.from_asset("deployment/dist/lambda/stepfunction.zip"),
            description="CMS Vehicle Simulator Function",
            environment={
                "IOT_ENDPOINT": self.iot_endpoint,
                "SOLUTION_ID": solution_config_inputs.solution_id,
                "VERSION": solution_config_inputs.solution_version,
                "ROUTE_BUCKET": routes_bucket.bucket_name,
                "SIM_TABLE": self.simulations_table_name,
                "TOPIC_PREFIX": iot_topic_prefix,
                "USER_AGENT_STRING": solution_config_inputs.get_user_agent_string(),
            },
            handler="function.handlers.data_sim_handler",
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            timeout=Duration.minutes(1),
            role=simulator_lambda_role,
            layers=[dependency_layer],
            vpc=vpc_construct.vpc,
            vpc_subnets=vpc_construct.private_subnet_selection,
            security_groups=[
                aws_ec2.SecurityGroup(
                    self,
                    "security-group-2",
                    vpc=vpc_construct.vpc,
                    allow_all_outbound=True,  # NOSONAR
                )
            ],
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
        )

        self.cleanup_lambda_function = aws_lambda.Function(
            self,
            "cleanup-lambda",
            function_name=cleanup_lambda_name,
            code=aws_lambda.Code.from_asset("deployment/dist/lambda/stepfunction.zip"),
            description="Provisioning Artifact Cleanup Function",
            environment={
                "IOT_ENDPOINT": self.iot_endpoint,
                "SOLUTION_ID": solution_config_inputs.solution_id,
                "VERSION": solution_config_inputs.solution_version,
                "SIMULATOR_THING_GROUP_NAME": simulator_thing_group_custom_resource.get_att(
                    "THING_GROUP_NAME"
                ).to_string(),
                "USER_AGENT_STRING": solution_config_inputs.get_user_agent_string(),
            },
            handler="function.handlers.cleanup_handler",
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            timeout=Duration.minutes(1),
            role=cleanup_lambda_role,
            layers=[dependency_layer],
            vpc=vpc_construct.vpc,
            vpc_subnets=vpc_construct.private_subnet_selection,
            security_groups=[
                aws_ec2.SecurityGroup(
                    self,
                    "security-group-3",
                    vpc=vpc_construct.vpc,
                    allow_all_outbound=True,  # NOSONAR
                )
            ],
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
        )

        self.done = aws_stepfunctions.Succeed(self, "Done")

        self.setup_step_function()

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

        simulator_log_group = aws_logs.LogGroup(
            self,
            "step-functions-log-group",
            removal_policy=RemovalPolicy.RETAIN,
            retention=aws_logs.RetentionDays.THREE_MONTHS,
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
