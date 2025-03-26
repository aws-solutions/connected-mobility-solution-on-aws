# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library

# AWS Libraries
from aws_cdk import CfnCondition, Fn, Stack, aws_iam
from constructs import Construct

# CMS Common Library
from cms_common.config.multi_account import MultiAccountConfig

# Connected Mobility Solution on AWS
from ..constructs.module_deploy import ModuleDeployCodeBuildConstruct
from ..constructs.module_integration import ModuleInputsConstruct


class MultiAccountConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        module_inputs: ModuleInputsConstruct,
        module_deploy_construct: ModuleDeployCodeBuildConstruct,
    ) -> None:
        super().__init__(scope, construct_id)

        should_create_policy = CfnCondition(
            self,
            "should-create-multi-account-policy",
            expression=Fn.condition_equals(
                module_inputs.backstage_multi_acct_setup_inputs.enable_multi_account_deployment,
                "true",
            ),
        )

        # Create policy
        multi_acct_policy = aws_iam.Policy(
            self,
            "multi-acct-policy",
            document=aws_iam.PolicyDocument(
                statements=[
                    aws_iam.PolicyStatement(
                        effect=aws_iam.Effect.ALLOW,
                        actions=["sts:AssumeRole"],
                        resources=[
                            Stack.of(self).format_arn(
                                service="iam",
                                resource="role",
                                account="*",
                                region="",
                                resource_name=f"{MultiAccountConfig.DEPLOYMENT_ROLE_NAME}-*",
                            )
                        ],
                    ),
                    aws_iam.PolicyStatement(
                        effect=aws_iam.Effect.ALLOW,
                        actions=["iam:PassRole"],
                        resources=[
                            Stack.of(self).format_arn(
                                service="iam",
                                resource="role",
                                account="*",
                                region="",
                                resource_name=f"{MultiAccountConfig.CLOUDFORMATION_ROLE_NAME}-*",
                            )
                        ],
                    ),
                ]
            ),
        )

        module_deploy_construct.codebuild_project.role.attach_inline_policy(  # type: ignore[union-attr]
            multi_acct_policy
        )

        multi_acct_policy.node.default_child.cfn_options.condition = (  # type: ignore[union-attr]
            should_create_policy
        )
