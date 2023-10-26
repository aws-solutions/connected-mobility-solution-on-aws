# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import datetime
from typing import Any, Dict
from unittest.mock import MagicMock

# Third Party Libraries
import pytest
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.stub import Stubber

# Connected Mobility Solution on AWS
from ....infrastructure.handlers.custom_resource.custom_resource import (
    CustomResourceTypes,
    create_deployment_uuid,
    get_proton_client,
    get_s3_client,
    handler,
)


def configure_s3_stubber(event: Dict[str, Any]) -> Any:
    stubbed_s3_client = get_s3_client()

    stubber = Stubber(stubbed_s3_client)

    stubber.add_response(
        "list_objects_v2",
        {
            "Name": event["ResourceProperties"]["TEMPLATE_S3_BUCKET_NAME"],
            "KeyCount": 1,
            "Contents": [
                {
                    "Key": "cms_environment_templates/cms_environment.tar.gz",
                }
            ],
        },
        {
            "Bucket": event["ResourceProperties"]["TEMPLATE_S3_BUCKET_NAME"],
            "Prefix": event["ResourceProperties"]["TEMPLATE_S3_KEY_PREFIX"],
            "StartAfter": event["ResourceProperties"]["TEMPLATE_S3_KEY_PREFIX"],
        },
    )

    stubber.activate()

    return stubbed_s3_client


def configure_proton_stubber(event: Dict[str, Any]) -> Any:
    stubbed_proton_client = get_proton_client()

    stubber = Stubber(stubbed_proton_client)

    stubber.add_response(
        "create_environment_template",
        {
            "environmentTemplate": {
                "arn": "arn:aws:proton:us-east-1:01234567890:environment-template/cms_environment",
                "name": "cms_environment",
                "displayName": "cms_environment",
                "createdAt": datetime.datetime.now(),
                "lastModifiedAt": datetime.datetime.now(),
            }
        },
        {"name": "cms_environment"},
    )

    stubber.add_response(
        "create_environment_template_version",
        {
            "environmentTemplateVersion": {
                "arn": "arn:aws:proton:us-east-1:01234567890:environment-template/cms_environment:1.0",
                "majorVersion": "1",
                "minorVersion": "0",
                "recommendedMinorVersion": "0",
                "status": "REGISTRATION_IN_PROGRESS",
                "templateName": "cms_environment",
                "createdAt": datetime.datetime.now(),
                "lastModifiedAt": datetime.datetime.now(),
            },
        },
        {
            "source": {
                "s3": {
                    "bucket": event["ResourceProperties"]["TEMPLATE_S3_BUCKET_NAME"],
                    "key": "cms_environment_templates/cms_environment.tar.gz",
                }
            },
            "templateName": "cms_environment",
            "majorVersion": "1",
        },
    )

    stubber.add_response(
        "get_environment_template_version",
        {
            "environmentTemplateVersion": {
                "majorVersion": "1",
                "minorVersion": "0",
                "status": "DRAFT",
                "arn": "DUMMY",
                "createdAt": datetime.datetime.now(),
                "lastModifiedAt": datetime.datetime.now(),
                "templateName": "cms_environment",
            }
        },
        {"templateName": "cms_environment", "majorVersion": "1", "minorVersion": "0"},
    )

    stubber.add_response(
        "update_environment_template_version",
        {
            "environmentTemplateVersion": {
                "templateName": "cms_environment",
                "majorVersion": "1",
                "minorVersion": "0",
                "status": "PUBLISHED",
                "arn": "arn",
                "createdAt": datetime.datetime.now(),
                "lastModifiedAt": datetime.datetime.now(),
            }
        },
        {
            "templateName": "cms_environment",
            "majorVersion": "1",
            "minorVersion": "0",
            "status": "PUBLISHED",
        },
    )

    stubber.add_client_error(
        "get_environment",
        expected_params={"name": "cms_environment"},
        service_error_code="ResourceNotFoundException",
        http_status_code=400,
    )

    if event["RequestType"] == CustomResourceTypes.RequestTypes.CREATE.value:

        stubber.add_response(
            "create_environment",
            {
                "environment": {
                    "deploymentStatus": "IN_PROGRESS",
                    "name": "cms_environment",
                    "templateName": "cms_environment",
                    "arn": "DUMMY",
                    "createdAt": datetime.datetime.now(),
                    "lastDeploymentAttemptedAt": datetime.datetime.now(),
                    "lastDeploymentSucceededAt": datetime.datetime.now(),
                    "templateMajorVersion": "1",
                    "templateMinorVersion": "0",
                }
            },
            {
                "name": "cms_environment",
                "templateName": "cms_environment",
                "templateMajorVersion": "1",
                "templateMinorVersion": "0",
                "spec": "{proton: EnvironmentSpec, spec: {a_number: 123}}",
                "codebuildRoleArn": event["ResourceProperties"]["CODE_BUILD_IAM_ROLE"],
            },
        )

    if event["RequestType"] == CustomResourceTypes.RequestTypes.UPDATE.value:
        stubber.add_response(
            "update_environment",
            {
                "environment": {
                    "deploymentStatus": "IN_PROGRESS",
                    "name": "cms_environment",
                    "templateName": "cms_environment",
                    "arn": "DUMMY",
                    "createdAt": datetime.datetime.now(),
                    "lastDeploymentAttemptedAt": datetime.datetime.now(),
                    "lastDeploymentSucceededAt": datetime.datetime.now(),
                    "templateMajorVersion": "1",
                    "templateMinorVersion": "0",
                }
            },
            {
                "name": "cms_environment",
                "templateMajorVersion": "1",
                "templateMinorVersion": "0",
                "deploymentType": "MINOR_VERSION",
                "spec": "{proton: EnvironmentSpec, spec: {a_number: 123}}",
                "codebuildRoleArn": event["ResourceProperties"]["CODE_BUILD_IAM_ROLE"],
            },
        )

    stubber.activate()

    return stubbed_proton_client


@pytest.fixture(name="custom_resource_s3_stub", scope="function")
def fixture_custom_resource_s3_stub(custom_resource_event: Dict[str, Any]) -> Any:
    return configure_s3_stubber(custom_resource_event)


@pytest.fixture(name="custom_resource_proton_stub", scope="function")
def fixture_custom_resource_proton_stub(custom_resource_event: Dict[str, Any]) -> Any:
    return configure_proton_stubber(custom_resource_event)


def test_handler(
    custom_resource_create_event: Dict[str, Any],
    context: LambdaContext,
    mocker: MagicMock,
    custom_resource_s3_stub: Any,
    custom_resource_proton_stub: Any,
) -> None:
    mocked_requests: MagicMock = mocker.patch(
        "requests.put",
    )

    expected_response = {
        "Status": "SUCCESS",
        "Data": {},
    }

    response = handler(custom_resource_create_event, context)

    mocked_requests.assert_called_once()

    assert response == expected_response


def test_create_deployment_uuid(
    custom_resource_create_deployment_uuid_event: Dict[str, Any]
) -> None:
    response = create_deployment_uuid(custom_resource_create_deployment_uuid_event)
    deployment_uuid = response["SolutionUUID"]
    assert isinstance(deployment_uuid, str)
    assert len(deployment_uuid) == 36
