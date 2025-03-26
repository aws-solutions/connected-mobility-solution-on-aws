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
from ..constructs.backstage_container import BackstageContainerConstruct
from ..constructs.module_integration import ModuleInputsConstruct


class MultiAccountConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        module_inputs: ModuleInputsConstruct,
        backstage_container_construct: BackstageContainerConstruct,
    ) -> None:
        super().__init__(scope, construct_id)

        is_multi_account_deployment_enabled = CfnCondition(
            self,
            "is-multi-account-enabled",
            expression=Fn.condition_equals(
                module_inputs.enable_multi_account_deployment_cfn_parameter,
                "true",
            ),
        )

        multi_acct_policy = aws_iam.Policy(
            self,
            "sts-multi-acct-policy",
            document=aws_iam.PolicyDocument(
                statements=[
                    aws_iam.PolicyStatement(
                        effect=aws_iam.Effect.ALLOW,
                        actions=["sts:AssumeRole"],
                        resources=[
                            Stack.of(self).format_arn(
                                service="iam",
                                resource="role",
                                region="",
                                account=module_inputs.backstage_account_directory_secrets.orgs_management_aws_account_id.string_value,
                                resource_name=MultiAccountConfig.ORGS_ACCOUNT_DIRECTORY_ASSUME_ROLE_NAME,
                            )
                        ],
                    )
                ]
            ),
        )

        backstage_container_construct.task_role.attach_inline_policy(multi_acct_policy)

        multi_acct_policy.node.default_child.cfn_options.condition = (  # type: ignore[union-attr]
            is_multi_account_deployment_enabled
        )
