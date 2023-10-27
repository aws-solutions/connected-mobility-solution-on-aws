# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
import pathlib
from io import TextIOWrapper
from os.path import abspath, dirname
from typing import Any, Optional

# Third Party Libraries
import toml
from aws_cdk import (
    ArnFormat,
    Aws,
    CfnOutput,
    CfnParameter,
    CfnResource,
    Fn,
    NestedStack,
    RemovalPolicy,
    Stack,
    Tags,
    aws_iam,
    aws_kms,
    aws_lambda,
    aws_logs,
    aws_ssm,
)
from chalice.cdk import Chalice
from constructs import Construct

# Connected Mobility Solution on AWS
from ..config.constants import VSConstants
from ..infrastructure import fetch_ssm_parameter
from ..infrastructure.constructs.app_registry import AppRegistryConstruct
from .aspects.validation import apply_validations
from .components.cloudfront import CloudFrontConstruct
from .components.cognito import CognitoConstruct
from .components.configuration import StackConfig
from .components.console import ConsoleConstruct
from .components.custom_resource import CustomResourcesConstruct
from .components.simulator import SimulatorConstruct
from .components.storage import StorageConstruct


class CmsVehicleSimulatorOnAwsStack(Stack):
    def __init__(self, scope: Construct, stack_id: str, **kwargs: Any) -> None:
        super().__init__(scope, stack_id, **kwargs)

        deployment_uuid = aws_ssm.StringParameter.from_string_parameter_name(
            self,
            "deployment-uuid",
            f"/{VSConstants.STAGE}/cms/common/config/deployment-uuid",
        ).string_value

        vehicle_simulator_construct = CmsVehicleSimulatorConstruct(
            self, "cms-vehicle-simulator"
        )

        Tags.of(vehicle_simulator_construct).add(
            "Solutions:DeploymentUUID", deployment_uuid
        )


class CmsVehicleSimulatorConstruct(Construct):
    stack_config = None

    def __init__(self, scope: Stack, stack_id: str) -> None:
        super().__init__(scope, stack_id)

        AppRegistryConstruct(
            self,
            "cms-vehicle-simulator-app-registry",
            application_name=VSConstants.APP_NAME,
            application_type=VSConstants.APPLICATION_TYPE,
            solution_id=VSConstants.SOLUTION_ID,
            solution_name=VSConstants.SOLUTION_NAME,
            solution_version=VSConstants.SOLUTION_VERSION,
        )

        self.admin_email = CfnParameter(
            Stack.of(self),
            "user-email",
            type="String",
            description="The user E-Mail to access the UI",
            allowed_pattern="^[_A-Za-z0-9-\\+]+(\\.[_A-Za-z0-9-]+)*@[A-Za-z0-9-]+(\\.[A-Za-z0-9]+)*(\\.[A-Za-z]{2,})$",
            constraint_description="User E-Mail must be a valid E-Mail address",
        )

        scope.template_options.template_format_version = "2010-09-09"
        scope.template_options.metadata = {
            "AWS::CloudFormation::Interface": {
                "ParameterGroups": [
                    {
                        "Label": {"default": "Console access"},
                        "Parameters": [self.admin_email.logical_id],
                    }
                ],
                "ParameterLabels": {
                    self.admin_email.logical_id: {
                        "default": "* Console Administrator Email"
                    }
                },
            }
        }

        self.general_stack = InfrastructureGeneralStack(
            self,
            "general-stack",
            admin_email=self.admin_email.value_as_string,
            description=(
                f"({VSConstants.SOLUTION_ID}-{VSConstants.CAPABILITY_ID}) "
                f"{VSConstants.SOLUTION_NAME} - Vehicle Simulator (General). "
                f"Version {VSConstants.SOLUTION_VERSION}"
            ),
        )

        self.cloudfront_stack = InfrastructureCloudFrontStack(
            self,
            "cloudfront-stack",
            description=(
                f"({VSConstants.SOLUTION_ID}-{VSConstants.CAPABILITY_ID}) "
                f"{VSConstants.SOLUTION_NAME} - Vehicle Simulator (CloudFront). "
                f"Version {VSConstants.SOLUTION_VERSION}"
            ),
        )

        self.cognito_stack = InfrastructureCognitoStack(
            self,
            "cognito-stack",
            description=(
                f"({VSConstants.SOLUTION_ID}-{VSConstants.CAPABILITY_ID}) "
                f"{VSConstants.SOLUTION_NAME} - Vehicle Simulator (Cognito). "
                f"Version {VSConstants.SOLUTION_VERSION}"
            ),
        )
        self.cognito_stack.add_dependency(self.cloudfront_stack)

        self.resource_stack = InfrastructureResourceStack(
            self,
            "custom-resources-stack",
            description=(
                f"({VSConstants.SOLUTION_ID}-{VSConstants.CAPABILITY_ID}) "
                f"{VSConstants.SOLUTION_NAME} - Vehicle Simulator (Resource). "
                f"Version {VSConstants.SOLUTION_VERSION}"
            ),
            solution_id=self.general_stack.stack_config.solution_id,
            solution_version=self.general_stack.stack_config.solution_version,
        )
        self.resource_stack.add_dependency(self.cognito_stack)
        self.resource_stack.add_dependency(self.general_stack)

        self.simulator_stack = InfrastructureSimulatorStack(
            self,
            "simulator-stack",
            description=(
                f"({VSConstants.SOLUTION_ID}-{VSConstants.CAPABILITY_ID}) "
                f"{VSConstants.SOLUTION_NAME} - Vehicle Simulator (Simulator). "
                f"Version {VSConstants.SOLUTION_VERSION}"
            ),
        )
        self.simulator_stack.add_dependency(self.general_stack)
        self.simulator_stack.add_dependency(self.resource_stack)

        self.vsapi_stack = VSApiStack(
            self,
            "vs-api-stack",
            description=(
                f"({VSConstants.SOLUTION_ID}-{VSConstants.CAPABILITY_ID}) "
                f"{VSConstants.SOLUTION_NAME} - Vehicle Simulator (VS API). "
                f"Version {VSConstants.SOLUTION_VERSION}"
            ),
        )
        self.vsapi_stack.add_dependency(self.cloudfront_stack)
        self.vsapi_stack.add_dependency(self.general_stack)
        self.vsapi_stack.add_dependency(self.simulator_stack)

        api_handler = (
            self.vsapi_stack.node.find_child("vs-api-chalice")
            .node.find_child("ChaliceApp")
            .node.find_child("APIHandler")
        )

        CfnResource.add_metadata(
            api_handler,  # type: ignore[arg-type]
            "cfn_nag",
            {
                "rules_to_suppress": [
                    {"id": "W89", "reason": "Ignore VPC requirements for now"},
                    {
                        "id": "W92",
                        "reason": "Ignore reserved concurrent executions for now",
                    },
                ]
            },
        )

        self.console_stack = InfrastructureConsoleStack(
            self,
            "console-stack",
            description=(
                f"({VSConstants.SOLUTION_ID}-{VSConstants.CAPABILITY_ID}) "
                f"{VSConstants.SOLUTION_NAME} - Vehicle Simulator (Console). "
                f"Version {VSConstants.SOLUTION_VERSION}"
            ),
        )
        self.console_stack.add_dependency(self.general_stack)
        self.console_stack.add_dependency(self.vsapi_stack)
        self.console_stack.add_dependency(self.resource_stack)
        self.console_stack.add_dependency(self.simulator_stack)

        apply_validations(scope)

        CfnOutput(
            self,
            "console-client-id",
            description="The console client ID",
            value=self.cognito_stack.cognito.user_pool_client.user_pool_client_id,
        )
        CfnOutput(
            self,
            "identity-pool-id",
            description="The ID for the Cognitio Identity Pool",
            value=self.cognito_stack.cognito.identity_pool.ref,
        )
        CfnOutput(
            self,
            "user-pool-id",
            description="User Pool Id",
            value=self.cognito_stack.cognito.user_pool.user_pool_id,
        )
        CfnOutput(
            self,
            "rest-api-id",
            description="API Gateway API ID",
            value=self.vsapi_stack.chalice.sam_template.get_resource("RestAPI").ref,
        )
        CfnOutput(
            self,
            "console-url",
            description="Console URL",
            value=f"https://{self.cloudfront_stack.cloudfront.console_cloudfront_dist.cloud_front_web_distribution.domain_name}",
        )
        CfnOutput(
            self,
            "cloudfront-distribution-bucket-name",
            description="Cloudfront Distribution Bucket Name",
            value=self.cloudfront_stack.cloudfront.console_cloudfront_dist.s3_bucket.bucket_name,  # type: ignore
        )
        CfnOutput(
            self,
            "admin-user-email",
            description="UserEmail",
            value=self.admin_email.value_as_string,
        )
        CfnOutput(
            self,
            "VSConstants.STAGE",
            description="Deployment stage",
            value=VSConstants.STAGE,
        )

        Tags.of(self).add(
            "solution-id", self.general_stack.stack_config.solution_id or "N/A"
        )


class InfrastructureGeneralStack(NestedStack):
    def __init__(
        self,
        scope: CmsVehicleSimulatorConstruct,
        stack_id: str,
        admin_email: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, stack_id, **kwargs)

        self.stack_config = StackConfig(self, "configuration")

        self.storage = StorageConstruct(self, "storage")

        self.dependency_layer = self.package_dependency_layer(
            dir_path=f"{os.getcwd()}/{self.node.try_get_context('app_location')}/{self.node.try_get_context('dep_layer_name')}",
        )

        self.export_value(
            admin_email, name=f"{self.nested_stack_parent.artifact_id}-admin-email"  # type: ignore
        )

    def package_dependency_layer(
        self,
        dir_path: str = dirname(abspath(__file__)),
    ) -> aws_lambda.LayerVersion:
        source_pipfile = f"{dirname(dirname(dirname(abspath(__file__))))}/Pipfile"
        pip_path = f"{dir_path}/python"

        # Create the folders out to the build directory
        pathlib.Path(pip_path).mkdir(parents=True, exist_ok=True)
        requirements = f"{dir_path}/requirements.txt"

        # Copy Pipfile to build directory as requirements.txt format and excluding the large packages
        with open(source_pipfile, "r", encoding="utf-8") as pipfile:
            new_pipfile = toml.load(pipfile)
        with open(requirements, "w", encoding="utf-8") as requirements_file:

            for package, constraint in new_pipfile["packages"].items():
                if package not in ["boto3", "aws-cdk-lib", "chalice"]:
                    self.req_formatter(
                        package=package,
                        constraint=constraint,
                        requirements_file=requirements_file,
                    )

        # Install the requirements in the build directory (CDK will use this whole folder to build the zip)
        os.system(  # nosec
            f"/bin/bash -c 'python -m pip install -q --upgrade --target {pip_path} --requirement {requirements}'"
            # f" && find {dir_path} -name \\*.so -exec strip \\{{\\}} \\;'"
        )

        dependency_layer = aws_lambda.LayerVersion(
            self,
            f"{self.node.try_get_context('dep_layer_name')}-{VSConstants.STAGE}",
            code=aws_lambda.Code.from_asset(
                f"{os.getcwd()}/{self.node.try_get_context('app_location')}/{self.node.try_get_context('dep_layer_name')}"
            ),
            compatible_architectures=[
                aws_lambda.Architecture.X86_64,
                aws_lambda.Architecture.ARM_64,
            ],
            compatible_runtimes=[
                aws_lambda.Runtime.PYTHON_3_8,
                aws_lambda.Runtime.PYTHON_3_9,
                aws_lambda.Runtime.PYTHON_3_10,
            ],
        )
        aws_ssm.StringParameter(
            self,
            "lambda-dependency-layer-arn",
            string_value=dependency_layer.layer_version_arn,
            description="Arn for general dependency layer",
            parameter_name=f"/{VSConstants.STAGE}/{VSConstants.APP_NAME}/arns/dependency-layer-arn",
        )

        return dependency_layer

    def req_formatter(
        self, package: str, constraint: Any, requirements_file: TextIOWrapper
    ) -> None:
        if constraint == "*":
            requirements_file.write(package + "\n")
        else:
            try:
                extras = (
                    str(constraint.get("extras", "all"))
                    .replace("'", "")
                    .replace('"', "")
                )

                # Requirements.txt wildcards are done by not specifying a version, replace with empty string instead
                version = constraint["version"] if constraint["version"] != "*" else ""

                requirements_file.write(f"{package}{extras} {version}\n")
            except (TypeError, KeyError, AttributeError):
                if isinstance(constraint, str):
                    requirements_file.write(f"{package} {constraint}\n")


class InfrastructureCloudFrontStack(NestedStack):
    def __init__(
        self, scope: CmsVehicleSimulatorConstruct, stack_id: str, **kwargs: Any
    ) -> None:
        super().__init__(scope, stack_id, **kwargs)

        self.cloudfront = CloudFrontConstruct(self, "cloudfront-construct")


class InfrastructureSimulatorStack(NestedStack):
    def __init__(
        self, scope: CmsVehicleSimulatorConstruct, stack_id: str, **kwargs: Any
    ) -> None:
        super().__init__(scope, stack_id, **kwargs)

        self.simulator = SimulatorConstruct(self, "simulator-construct")


class InfrastructureCognitoStack(NestedStack):
    def __init__(
        self, scope: CmsVehicleSimulatorConstruct, stack_id: str, **kwargs: Any
    ) -> None:
        super().__init__(scope, stack_id, **kwargs)

        self.cognito = CognitoConstruct(self, "cognito-construct")


class InfrastructureResourceStack(NestedStack):
    def __init__(
        self,
        scope: CmsVehicleSimulatorConstruct,
        stack_id: str,
        solution_id: Optional[str],
        solution_version: Optional[str],
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, stack_id, **kwargs)

        self.custom_resources = CustomResourcesConstruct(
            self,
            "custom-resources-construct",
            solution_id=solution_id,
            solution_version=solution_version,
        )


class InfrastructureConsoleStack(NestedStack):
    def __init__(
        self,
        scope: CmsVehicleSimulatorConstruct,
        stack_id: str,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, stack_id, **kwargs)

        api_id = fetch_ssm_parameter(
            self,
            "rest-api-id",
            f"/{VSConstants.STAGE}/{VSConstants.APP_NAME}/ids/chalice-rest-api-id",
        )

        api_endpoint = fetch_ssm_parameter(
            self,
            "rest-api-endpoint",
            f"/{VSConstants.STAGE}/{VSConstants.APP_NAME}/chalice-rest-api-endpoint",
        )

        template_folder_path = os.path.join(
            "source", "infrastructure", "assets", "templates"
        )
        self.console = ConsoleConstruct(
            self,
            "console-construct",
            template_folder_path=template_folder_path,
            api_id=api_id,
            api_endpoint=api_endpoint,
        )


class VSApiStack(NestedStack):
    def __init__(
        self, scope: CmsVehicleSimulatorConstruct, stack_id: str, **kwargs: Any
    ):
        super().__init__(scope, stack_id, **kwargs)

        api_log_group_kms_key = aws_kms.Key(
            self,
            "vs-api-log-group-kms-key",
            alias="vs-api-log-group-kms-key",
            enable_key_rotation=True,
        )

        self.api_log_group = aws_logs.LogGroup(
            self,
            "vs-api-log-group",
            removal_policy=RemovalPolicy.RETAIN,
            retention=aws_logs.RetentionDays.THREE_MONTHS,
            encryption_key=api_log_group_kms_key,
        )

        api_log_group_kms_key.add_to_resource_policy(
            statement=aws_iam.PolicyStatement(
                effect=aws_iam.Effect.ALLOW,
                principals=[
                    aws_iam.ServicePrincipal(f"logs.{self.region}.amazonaws.com")
                ],
                actions=["kms:Encrypt", "kms:Decrypt", "kms:GenerateDataKey"],
                resources=["*"],
            )
        )

        devices_types_table_arn = fetch_ssm_parameter(
            self,
            "ssm-devices-types-table-arn",
            f"/{VSConstants.STAGE}/{VSConstants.APP_NAME}/dynamodb/devices-types-table-arn",
        )
        templates_table_arn = fetch_ssm_parameter(
            self,
            "ssm-templates-table-arn",
            f"/{VSConstants.STAGE}/{VSConstants.APP_NAME}/dynamodb/templates-table-arn",
        )
        simulations_table_arn = fetch_ssm_parameter(
            self,
            "ssm-simulations-table-arn",
            f"/{VSConstants.STAGE}/{VSConstants.APP_NAME}/dynamodb/simulations-table-arn",
        )
        device_types_table_name = fetch_ssm_parameter(
            self,
            "ssm-devices-types-table-name",
            f"/{VSConstants.STAGE}/{VSConstants.APP_NAME}/dynamodb/devices-types-table-name",
        )
        templates_table_name = fetch_ssm_parameter(
            self,
            "ssm-templates-table-name",
            f"/{VSConstants.STAGE}/{VSConstants.APP_NAME}/dynamodb/templates-table-name",
        )
        simulations_table_name = fetch_ssm_parameter(
            self,
            "ssm-simulations-table-name",
            f"/{VSConstants.STAGE}/{VSConstants.APP_NAME}/dynamodb/simulations-table-name",
        )
        simulator_state_machine_name = fetch_ssm_parameter(
            self,
            "ssm-state-machine-name",
            f"/{VSConstants.STAGE}/{VSConstants.APP_NAME}/names/simulator-state-machine-name",
        )
        simulator_state_machine_arn = fetch_ssm_parameter(
            self,
            "ssm-state-machine-arn",
            f"/{VSConstants.STAGE}/{VSConstants.APP_NAME}/arns/simulator-state-machine-arn",
        )

        self.vs_api_lambda_role = aws_iam.Role(
            self,
            "vs-api-lambda-role",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            path="/",
            inline_policies={
                "api-cloudwatch-logs-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "logs:CreateLogGroup",
                                "logs:CreateLogStream",
                                "logs:PutLogEvents",
                            ],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="logs",
                                    resource="log-group",
                                    resource_name="/aws/lambda/*",
                                    arn_format=ArnFormat.COLON_RESOURCE_NAME,
                                )
                            ],
                        ),
                    ]
                ),
                "dynamodb-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "dynamodb:GetItem",
                                "dynamodb:Scan",
                                "dynamodb:PutItem",
                                "dynamodb:DeleteItem",
                                "dynamodb:UpdateItem",
                            ],
                            resources=[
                                devices_types_table_arn,
                                simulations_table_arn,
                                templates_table_arn,
                            ],
                        )
                    ]
                ),
                "state-machine-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=["states:StartExecution", "states:StopExecution"],
                            resources=[
                                simulator_state_machine_arn,
                                Stack.of(self).format_arn(
                                    service="states",
                                    resource="execution",
                                    resource_name=simulator_state_machine_name + ":*",
                                    arn_format=ArnFormat.COLON_RESOURCE_NAME,
                                ),
                            ],
                        ),
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "states:ListStateMachines",
                            ],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="states",
                                    resource="stateMachine",
                                    resource_name="*",
                                    arn_format=ArnFormat.COLON_RESOURCE_NAME,
                                )
                            ],
                        ),
                    ]
                ),
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
                            actions=[
                                "iot:DetachThingPrincipal",
                                "iot:ListThings",
                                "iot:ListThingPrincipals",
                                "iot:ListAttachedPolicies",
                            ],
                            resources=["*"],
                        ),
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "iot:DetachPolicy",
                                "iot:DeleteCertificate",
                            ],
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
                "tags-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "tag:GetResources",
                            ],
                            resources=["*"],
                        )
                    ]
                ),
                "secrets-manager-policy": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "secretsmanager:DeleteSecret",
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
            },
        )

        cross_origin_domain = (
            "*"
            if VSConstants.STAGE == "local"
            else "https://"
            + Fn.import_value(f"{VSConstants.APP_NAME}-cloud-front-domain-name")
        )

        self.chalice = Chalice(
            self,
            "vs-api-chalice",
            source_dir=os.path.join(
                os.path.dirname(__file__),
                os.pardir,
                "handlers",
                "api",
                "vs_api",
            ),
            stage_config={
                "environment_variables": {
                    "DYN_DEVICE_TYPES_TABLE": device_types_table_name,
                    "DYN_TEMPLATES_TABLE": templates_table_name,
                    "DYN_SIMULATIONS_TABLE": simulations_table_name,
                    "SIMULATOR_STATE_MACHINE_NAME": simulator_state_machine_name,
                    "CROSS_ORIGIN_DOMAIN": cross_origin_domain,
                    "USER_POOL_ARN": Fn.import_value(
                        f"{VSConstants.APP_NAME}-user-pool-arn"
                    ),
                    "USER_AGENT_STRING": VSConstants.USER_AGENT_STRING,
                },
                "manage_iam_role": False,
                "iam_role_arn": self.vs_api_lambda_role.role_arn,
                "api_gateway_stage": VSConstants.STAGE,
                "api_gateway_endpoint_type": "REGIONAL",
            },
        )

        aws_ssm.StringParameter(
            self,
            "rest-api-id",
            string_value=self.chalice.sam_template.get_resource("RestAPI").ref,
            description="Rest API Id of rest api created by chalice",
            parameter_name=f"/{VSConstants.STAGE}/{VSConstants.APP_NAME}/ids/chalice-rest-api-id",
        )
        aws_ssm.StringParameter(
            self,
            "rest-api-endpoint",
            string_value=f"https://{self.chalice.sam_template.get_resource('RestAPI').ref}.execute-api.{Stack.of(self).region}.{Aws.URL_SUFFIX}/{VSConstants.STAGE}",
            description="Rest API Endpoint of rest api created by chalice",
            parameter_name=f"/{VSConstants.STAGE}/{VSConstants.APP_NAME}/chalice-rest-api-endpoint",
        )
