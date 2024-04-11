# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any, Callable

# Third Party Libraries
import jsii

# AWS Libraries
from aws_cdk import (
    Annotations,
    Aspects,
    IAspect,
    Stack,
    Tokenization,
    aws_lambda,
    aws_s3,
)


def apply_validations(root_stack: Stack) -> None:
    for aspect in [SupportedLambdaRuntimes, BucketVersioningChecker]:
        Aspects.of(root_stack).add(aspect())  # type: ignore[arg-type]


def aspect_type_filter(
    node_type: Any,
) -> Callable[[Callable[..., Any]], Callable[[IAspect, Any], None]]:
    def decorator(function: Callable[..., Any]) -> Callable[[IAspect, Any], None]:
        def run_function(aspect: IAspect, node: Any) -> None:
            if isinstance(node, node_type):
                function(aspect, node)

        return run_function

    return decorator


@jsii.implements(IAspect)
class BucketVersioningChecker:
    @aspect_type_filter(node_type=aws_s3.CfnBucket)
    def visit(self, node: aws_s3.CfnBucket) -> None:
        # Check for versioning property, exclude the case where the property
        # can be a token (IResolvable).
        if (
            not node.versioning_configuration
            or not Tokenization.is_resolvable(node.versioning_configuration)
            and node.versioning_configuration.status != "Enabled"  # type: ignore
        ):
            Annotations.of(node).add_error("Bucket versioning is not enabled")


@jsii.implements(IAspect)
class SupportedLambdaRuntimes:
    supported_list = [
        aws_lambda.Runtime.PYTHON_3_8,
        aws_lambda.Runtime.PYTHON_3_9,
        aws_lambda.Runtime.PYTHON_3_10,
        aws_lambda.Runtime.NODEJS_14_X,
        aws_lambda.Runtime.NODEJS_16_X,
        aws_lambda.Runtime.NODEJS_18_X,
    ]

    @aspect_type_filter(aws_lambda.Function)
    def visit(self, node: aws_lambda.Function) -> None:
        if not any(
            runtime.runtime_equals(node.runtime)  # pylint: disable=E1101
            for runtime in self.supported_list
        ):
            Annotations.of(node).add_error(
                (
                    f"Lambda Runtime ({node.runtime.to_string()}) not supported."  # pylint: disable=E1101
                    f" Supported list {[sup.to_string() for sup in self.supported_list]}"  # pylint: disable=E1101
                )
            )
