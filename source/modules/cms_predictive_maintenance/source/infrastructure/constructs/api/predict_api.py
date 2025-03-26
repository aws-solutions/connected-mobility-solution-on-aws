# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# AWS Libraries
from aws_cdk import (
    ArnFormat,
    Duration,
    Stack,
    aws_apigateway,
    aws_ec2,
    aws_iam,
    aws_lambda,
    aws_logs,
)
from aws_solutions_constructs.aws_apigateway_lambda import ApiGatewayToLambda
from constructs import Construct

# CMS Common Library
from cms_common.config.resource_names import ResourceName, ResourcePrefix
from cms_common.config.stack_inputs import SolutionConfigInputs
from cms_common.constructs.encrypted_s3 import EncryptedS3Construct
from cms_common.constructs.vpc_construct import VpcConstruct
from cms_common.policy_generators.cloudwatch import (
    generate_lambda_cloudwatch_logs_policy_document,
)
from cms_common.policy_generators.ec2_vpc import generate_ec2_vpc_policy

# Connected Mobility Solution on AWS
from .authorization_lambda import AuthorizationLambdaConstruct
from .interface import BatchInferenceConfig, PredictApiOutputs


class PredictApiConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_unique_id: str,
        solution_config_inputs: SolutionConfigInputs,
        dependency_layer: aws_lambda.LayerVersion,
        vpc_construct: VpcConstruct,
        authorization_lambda_construct: AuthorizationLambdaConstruct,
        sagemaker_model_endpoint_name: str,
        sagemaker_assets_bucket_construct: EncryptedS3Construct,
        batch_inference_config: BatchInferenceConfig,
    ) -> None:
        super().__init__(scope, construct_id)

        predict_api_lambda_name = ResourceName.hyphen_separated(
            prefix=ResourcePrefix.hyphen_separated(
                app_unique_id=app_unique_id,
                module_name=solution_config_inputs.module_short_name,
            ),
            name="predict-api",
        )

        self.role = aws_iam.Role(
            self,
            "lambda-role",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            inline_policies={
                "lambda-logs-policy": generate_lambda_cloudwatch_logs_policy_document(
                    self, predict_api_lambda_name
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
                "deployment/dist/lambda/predict_api.zip",
                exclude=["**/tests/*"],
            ),
            handler="function.main.handler",
            function_name=predict_api_lambda_name,
            role=self.role,
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            timeout=Duration.minutes(1),
            layers=[dependency_layer],
            memory_size=512,
            environment={
                "USER_AGENT_STRING": solution_config_inputs.get_user_agent_string(),
                "SAGEMAKER_MODEL_ENDPOINT_NAME": sagemaker_model_endpoint_name,
                "RESOURCE_NAME_SUFFIX": ResourcePrefix.hyphen_separated(
                    app_unique_id=app_unique_id,
                    module_name=solution_config_inputs.module_short_name,
                ),
                "BATCH_INFERENCE_DATA_OUTPUT_S3_KEY_PREFIX": batch_inference_config.data_s3_key_prefix,
                "BATCH_INFERENCE_DATA_S3_BUCKET_NAME": sagemaker_assets_bucket_construct.bucket.bucket_name,
                "BATCH_INFERENCE_INSTANCE_TYPE": batch_inference_config.instance_type,
                "BATCH_INFERENCE_INSTANCE_COUNT": str(
                    batch_inference_config.instance_count
                ),
            },
            log_retention=aws_logs.RetentionDays.THREE_MONTHS,
            vpc=vpc_construct.vpc,
            vpc_subnets=vpc_construct.private_subnet_selection,
            security_groups=[security_group],
        )

        api_lambda_integration = aws_apigateway.LambdaIntegration(
            self.function,
            passthrough_behavior=aws_apigateway.PassthroughBehavior.NEVER,
        )

        predict_api_name = ResourceName.hyphen_separated(
            prefix=ResourcePrefix.hyphen_separated(
                app_unique_id=app_unique_id,
                module_name=solution_config_inputs.module_short_name,
            ),
            name="rest-api",
        )

        apigateway_to_lambda = ApiGatewayToLambda(
            self,
            "api-gateway-to-lambda",
            existing_lambda_obj=self.function,
            api_gateway_props=aws_apigateway.LambdaRestApiProps(
                description="API to invoke the SageMaker prediction model.",
                handler=self.function,
                rest_api_name=predict_api_name,
                proxy=False,
                deploy_options=aws_apigateway.StageOptions(
                    logging_level=aws_apigateway.MethodLoggingLevel.INFO,
                    data_trace_enabled=False,
                    metrics_enabled=True,
                ),
            ),
        )
        self.api = apigateway_to_lambda.api_gateway

        request_validator = aws_apigateway.RequestValidator(
            self,
            "request-validator",
            rest_api=self.api,
            request_validator_name=f"{predict_api_name}-request-validator",
            validate_request_body=True,
            validate_request_parameters=True,
        )

        authorizer = aws_apigateway.RequestAuthorizer(
            self,
            "rest-api-authorizer",
            handler=authorization_lambda_construct.authorization_lambda,
            identity_sources=[aws_apigateway.IdentitySource.header("Authorization")],
            results_cache_ttl=Duration.seconds(0),
        )

        predict_resource = self.api.root.add_resource("predict")
        predict_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_headers=["*"],
            allow_methods=["POST"],
        )
        predict_resource.add_method(
            http_method="POST",
            operation_name="get-prediction",
            integration=api_lambda_integration,
            authorizer=authorizer,
            authorization_type=aws_apigateway.AuthorizationType.CUSTOM,
            request_validator=request_validator,
            request_parameters={
                "method.request.header.authorization": True,
            },
            request_models={
                "application/json": aws_apigateway.Model(
                    self,
                    "get-prediction-body-model",
                    rest_api=self.api,
                    content_type="application/json",
                    description="Invoke the predictive maintenance SageMaker model.",
                    model_name="GetPredictionBodyModel",
                    schema=aws_apigateway.JsonSchema(
                        schema=aws_apigateway.JsonSchemaVersion.DRAFT7,
                        type=aws_apigateway.JsonSchemaType.OBJECT,
                        properties={
                            "input": aws_apigateway.JsonSchema(
                                type=aws_apigateway.JsonSchemaType.STRING
                            ),
                        },
                        additional_properties=False,
                    ),
                ),
            },
            method_responses=[
                aws_apigateway.MethodResponse(
                    status_code="200",
                    response_models={
                        "application/json": aws_apigateway.Model(
                            self,
                            "get-prediction-response-model",
                            rest_api=self.api,
                            content_type="application/json",
                            description="Response to invoking the predictive maintenance SageMaker model.",
                            model_name="GetPredictionResponseModel",
                            schema=aws_apigateway.JsonSchema(
                                schema=aws_apigateway.JsonSchemaVersion.DRAFT7,
                                type=aws_apigateway.JsonSchemaType.OBJECT,
                                properties={
                                    "prediction": aws_apigateway.JsonSchema(
                                        type=aws_apigateway.JsonSchemaType.STRING
                                    ),
                                },
                                additional_properties=False,
                            ),
                        ),
                    },
                ),
            ],
        )
        self.function.add_to_role_policy(
            statement=aws_iam.PolicyStatement(
                actions=[
                    "sagemaker:InvokeEndpoint",
                ],
                effect=aws_iam.Effect.ALLOW,
                resources=[
                    Stack.of(self).format_arn(
                        service="sagemaker",
                        resource="endpoint",
                        resource_name=sagemaker_model_endpoint_name,
                        arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                    ),
                ],
            )
        )

        batch_predict_resource = self.api.root.add_resource("batch-predict")
        batch_predict_resource.add_cors_preflight(
            allow_origins=["*"],
            allow_headers=["*"],
            allow_methods=["POST", "GET"],
        )

        batch_predict_resource.add_method(
            http_method="POST",
            operation_name="start-batch-inference",
            integration=api_lambda_integration,
            authorizer=authorizer,
            authorization_type=aws_apigateway.AuthorizationType.CUSTOM,
            request_validator=request_validator,
            request_parameters={
                "method.request.header.authorization": True,
            },
            request_models={
                "application/json": aws_apigateway.Model(
                    self,
                    "start-batch-prediction-body-model",
                    rest_api=self.api,
                    content_type="application/json",
                    description="Invoke batch inference with the predictive maintenance SageMaker model.",
                    model_name="StartBatchPredictionBodyModel",
                    schema=aws_apigateway.JsonSchema(
                        schema=aws_apigateway.JsonSchemaVersion.DRAFT7,
                        type=aws_apigateway.JsonSchemaType.OBJECT,
                        properties={
                            "input_data_s3_key": aws_apigateway.JsonSchema(
                                type=aws_apigateway.JsonSchemaType.STRING
                            ),
                        },
                        additional_properties=False,
                    ),
                ),
            },
            method_responses=[
                aws_apigateway.MethodResponse(
                    status_code="200",
                    response_models={
                        "application/json": aws_apigateway.Model(
                            self,
                            "start-batch-prediction-response-model",
                            rest_api=self.api,
                            content_type="application/json",
                            description="Response to invoking batch inference on the predictive maintenance SageMaker model.",
                            model_name="StartBatchPredictionResponseModel",
                            schema=aws_apigateway.JsonSchema(
                                schema=aws_apigateway.JsonSchemaVersion.DRAFT7,
                                type=aws_apigateway.JsonSchemaType.OBJECT,
                                properties={
                                    "transform-job-name": aws_apigateway.JsonSchema(
                                        type=aws_apigateway.JsonSchemaType.STRING
                                    ),
                                },
                                additional_properties=False,
                            ),
                        ),
                    },
                ),
            ],
        )
        self.function.add_to_role_policy(
            statement=aws_iam.PolicyStatement(
                actions=[
                    "sagemaker:CreateTransformJob",
                ],
                effect=aws_iam.Effect.ALLOW,
                resources=[
                    Stack.of(self).format_arn(
                        service="sagemaker",
                        resource="transform-job",
                        resource_name="*",
                        arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                    ),
                ],
            )
        )
        self.function.add_to_role_policy(
            statement=aws_iam.PolicyStatement(
                actions=[
                    "sagemaker:ListModels",
                ],
                effect=aws_iam.Effect.ALLOW,
                resources=["*"],
            )
        )

        self._create_gateway_responses()

        self.outputs = PredictApiOutputs(
            endpoint_url=self.api.url,
        )

    def _create_gateway_responses(self) -> None:
        aws_apigateway.GatewayResponse(
            self,
            "bad-request-default-response",
            rest_api=self.api,
            type=aws_apigateway.ResponseType.DEFAULT_4_XX,
            response_headers={
                "gatewayresponse.header.Access-Control-Allow-Origin": "'*'",
                "gatewayresponse.header.Access-Control-Allow-Headers": "'*'",
            },
        )

        aws_apigateway.GatewayResponse(
            self,
            "internal-server-error-default-response",
            rest_api=self.api,
            type=aws_apigateway.ResponseType.DEFAULT_5_XX,
            status_code="500",
            response_headers={
                "gatewayresponse.header.Access-Control-Allow-Origin": "'*'",
                "gatewayresponse.header.Access-Control-Allow-Headers": "'*'",
            },
        )

        aws_apigateway.GatewayResponse(
            self,
            "bad-request-body-response",
            rest_api=self.api,
            type=aws_apigateway.ResponseType.BAD_REQUEST_BODY,
            status_code="400",
            response_headers={
                "gatewayresponse.header.Access-Control-Allow-Origin": "'*'",
                "gatewayresponse.header.Access-Control-Allow-Headers": "'*'",
            },
            templates={
                "application/json": '{"error":{"message":"$context.error.messageString","errors":"$context.error.validationErrorString"}}'
            },
        )

        aws_apigateway.GatewayResponse(
            self,
            "bad-request-parameter-response",
            rest_api=self.api,
            type=aws_apigateway.ResponseType.BAD_REQUEST_PARAMETERS,
            status_code="400",
            response_headers={
                "gatewayresponse.header.Access-Control-Allow-Origin": "'*'",
                "gatewayresponse.header.Access-Control-Allow-Headers": "'*'",
            },
            templates={
                "application/json": '{"error":{"message":"$context.error.messageString","errors":"$context.error.validationErrorString"}}'
            },
        )

        aws_apigateway.GatewayResponse(
            self,
            "throttling-requests-response",
            rest_api=self.api,
            type=aws_apigateway.ResponseType.THROTTLED,
            status_code="429",
            response_headers={
                "gatewayresponse.header.Access-Control-Allow-Origin": "'*'",
                "gatewayresponse.header.Access-Control-Allow-Headers": "'*'",
            },
            templates={
                "application/json": '{"error":{"message":"$context.error.messageString","errors":"$context.error.validationErrorString"}}'
            },
        )
