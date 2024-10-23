# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Sequence

# AWS Libraries
from aws_cdk import ArnFormat, Stack, aws_bedrock, aws_iam, aws_kms
from constructs import Construct

# CMS Common Library
from cms_common.config.resource_names import ResourceName, ResourcePrefix
from cms_common.config.stack_inputs import SolutionConfigInputs

# Connected Mobility Solution on AWS
from ..interface import AgentConfig


class BedrockAgentConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        app_unique_id: str,
        solution_config_inputs: SolutionConfigInputs,
        knowledge_base_id: str,
        agent_config: AgentConfig,
        action_groups: Sequence[aws_bedrock.CfnAgent.AgentActionGroupProperty],
    ) -> None:
        super().__init__(scope, construct_id)

        agent_name = ResourceName.hyphen_separated(
            prefix=ResourcePrefix.hyphen_separated(
                app_unique_id=app_unique_id,
                module_name=solution_config_inputs.module_short_name,
            ),
            name="agent",
        )

        agent_role = aws_iam.Role(
            self,
            "role",
            role_name=f"AmazonBedrockExecutionRoleForAgents-{app_unique_id}-{Stack.of(self).region}",
            assumed_by=aws_iam.ServicePrincipal("bedrock.amazonaws.com"),
            inline_policies={
                "foundational-model": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "bedrock:InvokeModel",
                            ],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="bedrock",
                                    resource="foundation-model",
                                    account="",
                                    resource_name=agent_config.foundational_model_id,
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                            ],
                        ),
                    ]
                ),
                "knowledge-base": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "bedrock:Retrieve",
                            ],
                            resources=[
                                Stack.of(self).format_arn(
                                    service="bedrock",
                                    resource="knowledge-base",
                                    resource_name=knowledge_base_id,
                                    arn_format=ArnFormat.SLASH_RESOURCE_NAME,
                                ),
                            ],
                        ),
                    ]
                ),
                "action-group": aws_iam.PolicyDocument(
                    statements=[
                        aws_iam.PolicyStatement(
                            effect=aws_iam.Effect.ALLOW,
                            actions=[
                                "lambda:InvokeFunction",
                            ],
                            resources=[
                                str(action_group.action_group_executor.lambda_)  # type: ignore[union-attr]
                                for action_group in action_groups
                            ],
                        ),
                    ]
                ),
            },
        )

        guardrail_key = aws_kms.Key(
            self,
            "guardrail-cmk-key",
            enable_key_rotation=True,
        )

        guardrail = aws_bedrock.CfnGuardrail(
            self,
            "guardrail",
            name=ResourceName.hyphen_separated(
                prefix=ResourcePrefix.hyphen_separated(
                    app_unique_id=app_unique_id,
                    module_name=solution_config_inputs.module_short_name,
                ),
                name="guardrail",
            ),
            kms_key_arn=guardrail_key.key_arn,
            blocked_input_messaging="Sorry, the model cannot answer this question.",
            blocked_outputs_messaging="Sorry, the model cannot answer this question.",
            content_policy_config=aws_bedrock.CfnGuardrail.ContentPolicyConfigProperty(
                filters_config=[
                    aws_bedrock.CfnGuardrail.ContentFilterConfigProperty(
                        input_strength="HIGH",
                        output_strength="HIGH",
                        type="HATE",
                    ),
                    aws_bedrock.CfnGuardrail.ContentFilterConfigProperty(
                        input_strength="HIGH",
                        output_strength="HIGH",
                        type="INSULTS",
                    ),
                    aws_bedrock.CfnGuardrail.ContentFilterConfigProperty(
                        input_strength="HIGH",
                        output_strength="HIGH",
                        type="SEXUAL",
                    ),
                    aws_bedrock.CfnGuardrail.ContentFilterConfigProperty(
                        input_strength="HIGH",
                        output_strength="HIGH",
                        type="VIOLENCE",
                    ),
                    aws_bedrock.CfnGuardrail.ContentFilterConfigProperty(
                        input_strength="HIGH",
                        output_strength="HIGH",
                        type="MISCONDUCT",
                    ),
                    aws_bedrock.CfnGuardrail.ContentFilterConfigProperty(
                        input_strength="HIGH",
                        output_strength="NONE",
                        type="PROMPT_ATTACK",
                    ),
                ]
            ),
        )

        agent_key = aws_kms.Key(
            self,
            "agent-cmk-key",
            enable_key_rotation=True,
        )

        self.agent = aws_bedrock.CfnAgent(
            self,
            "agent",
            agent_name=agent_name,
            auto_prepare=True,
            agent_resource_role_arn=agent_role.role_arn,
            skip_resource_in_use_check_on_delete=True,
            knowledge_bases=[
                aws_bedrock.CfnAgent.AgentKnowledgeBaseProperty(
                    description="Knowledge Base used to perform RAG.",
                    knowledge_base_id=knowledge_base_id,
                    knowledge_base_state="ENABLED",
                )
            ],
            foundation_model=agent_config.foundational_model_id,
            customer_encryption_key_arn=agent_key.key_arn,
            idle_session_ttl_in_seconds=agent_config.idle_session_ttl_in_seconds,
            instruction=agent_config.instruction,
            action_groups=action_groups,
            guardrail_configuration=aws_bedrock.CfnAgent.GuardrailConfigurationProperty(
                guardrail_identifier=guardrail.attr_guardrail_id,
                guardrail_version="DRAFT",
            ),
        )

        agent_alias_name = ResourceName.hyphen_separated(
            prefix=ResourcePrefix.hyphen_separated(
                app_unique_id=app_unique_id,
                module_name=solution_config_inputs.module_short_name,
            ),
            name="default-alias",
        )

        self.agent_alias = aws_bedrock.CfnAgentAlias(
            self,
            "agent-alias",
            agent_alias_name=agent_alias_name,
            agent_id=self.agent.attr_agent_id,
        )
