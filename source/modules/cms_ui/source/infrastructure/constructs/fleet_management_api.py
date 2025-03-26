# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
# Standard Library
import json
import os
import shutil
import subprocess  # nosec
from os.path import dirname
from typing import Any

# Third Party Libraries
import jsii

# AWS Libraries
from aws_cdk import (
    BundlingOptions,
    Duration,
    ILocalBundling,
    RemovalPolicy,
    Stack,
    aws_apigateway,
    aws_ec2,
    aws_iam,
    aws_lambda,
    aws_logs,
)
from constructs import Construct

# CMS Common Library
from cms_common.config.resource_names import ResourceName, ResourcePrefix
from cms_common.config.stack_inputs import SolutionConfigInputs
from cms_common.constructs.vpc_construct import VpcConstruct
from cms_common.policy_generators.cloudwatch import (
    generate_lambda_cloudwatch_logs_policy_document,
)
from cms_common.policy_generators.ec2_vpc import generate_ec2_vpc_policy
from cms_common.resource_names.physical_names import generate_physical_name

# Connected Mobility Solution on AWS
from .authorization_lambda import AuthorizationLambdaConstruct


@jsii.implements(ILocalBundling)
class TypeScriptLambdaBundling:
    def __init__(self, source_dir: str) -> None:
        self.source_dir = source_dir

    def try_bundle(self, output_dir: str, *args: Any, **kwargs: Any) -> bool:
        """Custom bundling command that runs locally using yarn"""

        os.chdir(self.source_dir)
        subprocess.run(["yarn", "install", "--no-immutable"], check=True)  # nosec
        subprocess.run(["yarn", "build"], check=True)  # nosec
        # fmt: off
        subprocess.run( # nosec
            ["yarn", "workspaces", "focus", "--production"], check=True
        )
        # fmt: on

        # Copy required files to output directory
        shutil.copytree(
            os.path.join(self.source_dir, "dist"), output_dir, dirs_exist_ok=True
        )
        shutil.copytree(
            os.path.join(self.source_dir, "node_modules"),
            os.path.join(output_dir, "node_modules"),
            dirs_exist_ok=True,
        )

        return True


class FleetManagementAPIConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_unique_id: str,
        solution_config_inputs: SolutionConfigInputs,
        authorization_lambda_construct: AuthorizationLambdaConstruct,
        vpc_construct: VpcConstruct,
        openapi_definition_path: str,
    ) -> None:
        super().__init__(scope, construct_id)

        fleet_management_lambda_name = ResourceName.hyphen_separated(
            prefix=ResourcePrefix.hyphen_separated(
                app_unique_id=app_unique_id,
                module_name=solution_config_inputs.module_short_name,
            ),
            name="fleet-api",
        )

        self.role = aws_iam.Role(
            self,
            "role",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            inline_policies={
                "fleetwise-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "iotfleetwise:ListFleets",
                                "iotfleetwise:GetFleet",
                                "iotfleetwise:ListVehicles",
                                "iotfleetwise:GetVehicle",
                                "iotfleetwise:ListCampaigns",
                                "iotfleetwise:ListVehiclesInFleet",
                                "iotfleetwise:ListFleetsForVehicle",
                                "iotfleetwise:ListSignalCatalogs",
                                "iotfleetwise:CreateFleet",
                                "iotfleetwise:DeleteFleet",
                                "iotfleetwise:DeleteCampaign",
                                "iotfleetwise:DeleteVehicle",
                                "iotfleetwise:DisassociateVehicleFleet",
                                "iotfleetwise:UpdateFleet",
                                "iotfleetwise:TagResource",
                                "iotfleetwise:ListTagsForResource",
                                "iotfleetwise:ListDecoderManifests",
                                "iotfleetwise:GetDecoderManifest",
                                "iotfleetwise:CreateVehicle",
                                "iotfleetwise:UpdateVehicle",
                                "iotfleetwise:AssociateVehicleFleet",
                                "iotfleetwise:GetCampaign",
                                "iotfleetwise:UpdateCampaign",
                            ],
                            resources=["*"],
                        ),
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "iot:ListThingPrincipals",
                                "iot:DeleteThing",
                                "iot:CreateThing",
                                "iot:DescribeThing",
                            ],
                            resources=["*"],
                        ),
                    ]
                ),
                "lambda-logs-policy": generate_lambda_cloudwatch_logs_policy_document(
                    self, fleet_management_lambda_name
                ),
                "ec2-policy": generate_ec2_vpc_policy(
                    self,
                    vpc_construct=vpc_construct,
                    subnet_selection=vpc_construct.private_subnet_selection,
                    authorized_service="lambda.amazonaws.com",
                ),
            },
        )

        security_group = aws_ec2.SecurityGroup(
            self,
            "security-group",
            vpc=vpc_construct.vpc,
            allow_all_outbound=True,  # NOSONAR
        )

        self.function = aws_lambda.Function(
            self,
            "lambda-function",
            code=aws_lambda.Code.from_asset(
                "source/handlers/fleet_management/",
                exclude=["**/node_modules/*"],
                bundling=BundlingOptions(
                    image=aws_lambda.Runtime.NODEJS_22_X.bundling_image,
                    command=[],
                    local=TypeScriptLambdaBundling(
                        source_dir=f"{dirname(dirname(dirname(__file__)))}/handlers/fleet_management"
                    ),
                ),
            ),
            handler="index.handler",
            function_name=fleet_management_lambda_name,
            role=self.role,
            runtime=aws_lambda.Runtime.NODEJS_22_X,
            timeout=Duration.minutes(1),
            memory_size=512,
            environment={
                "USER_AGENT_STRING": solution_config_inputs.get_user_agent_string(),
            },
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
            vpc=vpc_construct.vpc,
            vpc_subnets=vpc_construct.private_subnet_selection,
            security_groups=[security_group],
        )

        with open(openapi_definition_path, "r", encoding="utf-8") as f:
            openapi_definition = json.load(f)

        # add lambda function arn to the api gateway integrations
        for path in openapi_definition["paths"]:
            for operation in openapi_definition["paths"][path]:
                op = openapi_definition["paths"][path][operation]
                integration = op.get("x-amazon-apigateway-integration")

                if not integration:
                    raise ValueError(
                        f"No x-amazon-apigateway-integration for {op.get('operationId')}. "
                        "Make sure API Gateway integration is configured in the Smithy model."
                    )

                openapi_definition["paths"][path][operation][
                    "x-amazon-apigateway-integration"
                ][
                    "uri"
                ] = f"arn:{Stack.of(self).partition}:apigateway:{Stack.of(self).region}:lambda:path/2015-03-31/functions/{self.function.function_arn}/invocations"

        # add authorization lambda arn to the api gateway integrations
        openapi_definition["components"]["securitySchemes"]["LambdaOAuthAuthorizer"][
            "x-amazon-apigateway-authorizer"
        ][
            "authorizerUri"
        ] = f"arn:{Stack.of(self).partition}:apigateway:{Stack.of(self).region}:lambda:path/2015-03-31/functions/{authorization_lambda_construct.authorization_lambda.function_arn}/invocations"

        api_log_group = aws_logs.LogGroup(
            self,
            "step-functions-log-group",
            removal_policy=RemovalPolicy.RETAIN,
            retention=aws_logs.RetentionDays.THREE_MONTHS,
            log_group_name=generate_physical_name(
                scope=self,
                prefix="/aws/apigateway/",
                physical_name_substrings=[
                    Stack.of(self).stack_name,
                    self.node.scope.node.id,  # type: ignore
                    "api-log",
                ],
                max_length=512,
            ),
        )

        self.api = aws_apigateway.SpecRestApi(
            self,
            "fleet-management-api",
            api_definition=aws_apigateway.ApiDefinition.from_inline(openapi_definition),
            deploy_options=aws_apigateway.StageOptions(
                access_log_destination=aws_apigateway.LogGroupLogDestination(
                    api_log_group
                ),
                access_log_format=aws_apigateway.AccessLogFormat.json_with_standard_fields(
                    caller=True,
                    http_method=True,
                    ip=True,
                    protocol=True,
                    request_time=True,
                    resource_path=True,
                    response_length=True,
                    status=True,
                    user=True,
                ),
                logging_level=aws_apigateway.MethodLoggingLevel.INFO,
                data_trace_enabled=False,
                metrics_enabled=True,
                tracing_enabled=True,
            ),
        )

        self.function.add_permission(
            "ApiGatewayInvokesLambdaPermission",
            principal=aws_iam.ServicePrincipal("apigateway.amazonaws.com"),
            source_arn=self.api.arn_for_execute_api(),
        )

        authorization_lambda_construct.authorization_lambda.add_permission(
            "ApiGatewayInvokesAuthLambdaPermission",
            principal=aws_iam.ServicePrincipal("apigateway.amazonaws.com"),
            source_arn=f"arn:{Stack.of(self).partition}:execute-api:{Stack.of(self).region}:{Stack.of(self).account}:{self.api.rest_api_id}/authorizers/*",
        )
