# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# AWS Libraries
from aws_cdk import (
    Aspects,
    CfnCondition,
    Fn,
    RemovalPolicy,
    SecretValue,
    aws_secretsmanager,
)
from constructs import Construct

# CMS Common Library
from cms_common.aspects.condition import ConditionAspect


class OptionallyExistingSecret(Construct):
    def __init__(  # nosec
        self,
        scope: Construct,
        construct_id: str,
        secret_name: str,
        secret_string_value: SecretValue,
        description: str,
        removal_policy: RemovalPolicy,
        override_existing_secret_arn: str = "false",
        optional_existing_secret_arn: str = "",
    ) -> None:
        super().__init__(scope, construct_id)

        # Create new secret
        should_create_secret_condition = CfnCondition(
            self,
            "should-create-secret-condition",
            expression=Fn.condition_or(
                Fn.condition_equals(lhs=override_existing_secret_arn, rhs="true"),
                Fn.condition_equals(
                    lhs=optional_existing_secret_arn,
                    rhs="",
                ),
            ),
        )
        new_secret = aws_secretsmanager.Secret(
            self,
            "new-secret",
            description=description,
            removal_policy=removal_policy,
            secret_name=secret_name,
            secret_string_value=secret_string_value,
        )
        Aspects.of(new_secret).add(ConditionAspect(should_create_secret_condition))

        # Use existing secret
        should_use_existing_secret_condition = CfnCondition(
            self,
            "should-use-existing-secret-condition",
            expression=Fn.condition_and(
                Fn.condition_equals(lhs=override_existing_secret_arn, rhs="false"),
                Fn.condition_not(
                    condition=Fn.condition_equals(
                        lhs=optional_existing_secret_arn,
                        rhs="",
                    )
                ),
            ),
        )
        existing_secret = aws_secretsmanager.Secret.from_secret_complete_arn(
            self,
            "existing-secret",
            secret_complete_arn=optional_existing_secret_arn,
        )
        Aspects.of(existing_secret).add(
            ConditionAspect(should_use_existing_secret_condition)
        )

        self.secret_arn = Fn.condition_if(
            condition_id=should_create_secret_condition.logical_id,
            value_if_true=new_secret.secret_arn,
            value_if_false=existing_secret.secret_arn,
        ).to_string()
