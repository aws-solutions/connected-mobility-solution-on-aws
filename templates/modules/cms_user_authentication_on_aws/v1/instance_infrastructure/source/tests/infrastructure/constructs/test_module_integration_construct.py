# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library

# Third Party Libraries
from aws_cdk import Stack, assertions

# Connected Mobility Solution on AWS
from ....config.constants import UserAuthenticationConstants


def test_required_ssm_parameters_are_present(
    module_integration_stack: Stack,
) -> None:
    template = assertions.Template.from_stack(module_integration_stack)
    required_ssm_parameters = set(
        [
            f"/{UserAuthenticationConstants.STAGE}/cms/authentication/user-pool/region",
            f"/{UserAuthenticationConstants.STAGE}/cms/authentication/user-pool/domain-prefix",
            f"/{UserAuthenticationConstants.STAGE}/cms/authentication/service-client/id",
            f"/{UserAuthenticationConstants.STAGE}/cms/authentication/service-client-secret/secret-arn",
            f"/{UserAuthenticationConstants.STAGE}/cms/authentication/service-caller-scope/name",
            f"/{UserAuthenticationConstants.STAGE}/cms/authentication/resource-server/identifier",
            f"/{UserAuthenticationConstants.STAGE}/cms/authentication/create-app-client-lambda/arn",
            f"/{UserAuthenticationConstants.STAGE}/cms/authentication/update-app-client-lambda/arn",
            f"/{UserAuthenticationConstants.STAGE}/cms/authentication/delete-app-client-lambda/arn",
            f"/{UserAuthenticationConstants.STAGE}/cms/authentication/user-authentication-lambda/arn",
            f"/{UserAuthenticationConstants.STAGE}/cms/authentication/token-validation-lambda/arn",
        ]
    )

    ssm_parameter_resources_in_template = template.find_resources(
        type="AWS::SSM::Parameter"
    )
    ssm_parameters_in_template = set()
    for _, ssm_parameter in ssm_parameter_resources_in_template.items():
        ssm_parameters_in_template.add(ssm_parameter["Properties"]["Name"])

    assert required_ssm_parameters == ssm_parameters_in_template
