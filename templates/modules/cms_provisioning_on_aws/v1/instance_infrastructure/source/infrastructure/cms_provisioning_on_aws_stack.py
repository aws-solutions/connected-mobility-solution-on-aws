# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from typing import Any

# Third Party Libraries
from aws_cdk import Stack, Tags, aws_ssm
from constructs import Construct

# Connected Mobility Solution on AWS
from ..config.constants import VPConstants
from ..infrastructure.constructs.app_registry import AppRegistryConstruct
from .stacks.auxiliary_lambdas_stack import AuxiliaryLambdasStack
from .stacks.common_dependencies_stack import CommonDependenciesStack
from .stacks.iot_claim_provisioning_stack import IoTClaimProvisioningStack
from .stacks.provisioning_lambdas_stack import ProvisioningLambdasStack


class CmsProvisioningOnAwsStack(Stack):
    def __init__(self, scope: Construct, stack_id: str, **kwargs: Any) -> None:
        super().__init__(scope, stack_id, **kwargs)

        deployment_uuid = aws_ssm.StringParameter.from_string_parameter_name(
            self,
            "deployment-uuid",
            f"/{VPConstants.STAGE}/cms/common/config/deployment-uuid",
        ).string_value

        provisioning_construct = CmsProvisioningConstruct(self, "cms-provisioning")

        Tags.of(provisioning_construct).add("Solutions:DeploymentUUID", deployment_uuid)


class CmsProvisioningConstruct(Construct):
    def __init__(self, scope: Construct, stack_id: str) -> None:
        super().__init__(scope, stack_id)

        AppRegistryConstruct(
            self,
            "cms-provisioning-app-registry",
            application_name=VPConstants.APP_NAME,
            application_type=VPConstants.APPLICATION_TYPE,
            solution_id=VPConstants.SOLUTION_ID,
            solution_name=VPConstants.SOLUTION_NAME,
            solution_version=VPConstants.SOLUTION_VERSION,
        )

        self.common_dependencies_stack = CommonDependenciesStack(
            self,
            "common-dependencies-stack",
            description=(
                f"({VPConstants.SOLUTION_ID}-{VPConstants.CAPABILITY_ID}) "
                f"{VPConstants.SOLUTION_NAME} - Provisioning (Common Dependencies). "
                f"Version {VPConstants.SOLUTION_VERSION}"
            ),
        )

        self.provisioning_lambdas_stack = ProvisioningLambdasStack(
            self,
            "provisioning-lambdas-stack",
            description=(
                f"({VPConstants.SOLUTION_ID}-{VPConstants.CAPABILITY_ID}) "
                f"{VPConstants.SOLUTION_NAME} - Provisioning (Lambdas). "
                f"Version {VPConstants.SOLUTION_VERSION}"
            ),
        )
        self.provisioning_lambdas_stack.add_dependency(
            self.common_dependencies_stack,
        )

        self.auxiliary_lambdas_stack = AuxiliaryLambdasStack(
            self,
            "auxiliary-lambdas-stack",
            description=(
                f"({VPConstants.SOLUTION_ID}-{VPConstants.CAPABILITY_ID}) "
                f"{VPConstants.SOLUTION_NAME} - Provisioning (Auxiliary Lambdas). "
                f"Version {VPConstants.SOLUTION_VERSION}"
            ),
        )
        self.auxiliary_lambdas_stack.add_dependency(
            self.common_dependencies_stack,
        )
        self.auxiliary_lambdas_stack.add_dependency(
            self.provisioning_lambdas_stack,
        )

        self.iot_claim_provisioning_stack = IoTClaimProvisioningStack(
            self,
            "iot-claim-provisioning-stack",
            description=(
                f"({VPConstants.SOLUTION_ID}-{VPConstants.CAPABILITY_ID}) "
                f"{VPConstants.SOLUTION_NAME} - Provisioning (IoT Claim Provisioning). "
                f"Version {VPConstants.SOLUTION_VERSION}"
            ),
        )
        self.iot_claim_provisioning_stack.add_dependency(
            self.provisioning_lambdas_stack,
        )
        self.iot_claim_provisioning_stack.add_dependency(
            self.auxiliary_lambdas_stack,
        )
