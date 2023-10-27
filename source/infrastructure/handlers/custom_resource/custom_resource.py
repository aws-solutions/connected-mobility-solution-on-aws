# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json
import os
import time
import uuid
from enum import Enum
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Dict, Iterator, Tuple

# Third Party Libraries
import boto3
import requests
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.config import Config
from botocore.exceptions import ClientError

tracer = Tracer()
logger = Logger()

if TYPE_CHECKING:
    # Third Party Libraries
    from mypy_boto3_proton import ProtonClient
    from mypy_boto3_s3 import S3Client

else:
    S3Client = object
    ProtonClient = object

REMAINING_TIME_THRESHOLD = 10000  # milliseconds


@lru_cache(maxsize=128)
def get_s3_client() -> S3Client:
    return boto3.client(
        "s3", config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"])
    )


@lru_cache(maxsize=128)
def get_proton_client() -> ProtonClient:
    return boto3.client(
        "proton", config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"])
    )


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    response = {"Status": CustomResourceTypes.StatusTypes.SUCCESS.value, "Data": {}}
    reason = f"See the details in CloudWatch Log Stream: {context.log_stream_name}"

    try:

        match event["ResourceProperties"]["Resource"]:
            case CustomResourceTypes.ResourceTypes.CREATE_PROTON_ENVIRONMENT.value:
                create_proton_environment(event, context)
            case CustomResourceTypes.ResourceTypes.CREATE_DEPLOYMENT_UUID.value:
                response["Data"] = create_deployment_uuid(event)
            case _:
                raise KeyError(
                    f"No Custom Resource Type: {event['ResourceProperties']['Resource']}"
                )

    except Exception as exception:  # pylint: disable=W0703
        # Wrap all exceptions so CloudFormation doesn't hang
        logger.error("CustomResource error: %s", str(exception), exc_info=True)
        response["Status"] = CustomResourceTypes.StatusTypes.FAILED.value
        reason = f"{str(exception)} ... {reason}"

    send_cloud_formation_response(
        event,
        response,
        reason,
    )

    return response


@tracer.capture_method
def send_cloud_formation_response(
    event: Dict[str, Any], response: Dict[str, Any], reason: str
) -> None:
    response_body = {
        "Status": response["Status"],
        "Reason": reason,
        "PhysicalResourceId": event["LogicalResourceId"],
        "StackId": event["StackId"],
        "RequestId": event["RequestId"],
        "LogicalResourceId": event["LogicalResourceId"],
        "Data": response["Data"],
    }

    logger.info("response", extra={"response_body": response_body})

    headers = {"Content-Type": "application/json"}

    requests.put(
        event["ResponseURL"],
        data=json.dumps(response_body),
        headers=headers,
        timeout=60,
    )


@tracer.capture_method
def _get_s3_proton_templates(
    s3_bucket_name: str, s3_template_path_prefix: str
) -> Iterator[Tuple[str, str]]:
    # Add a trailing slash to the key prefix if it's not already included
    s3_template_prefix = os.path.join(s3_template_path_prefix, "")

    s3_response = get_s3_client().list_objects_v2(
        Bucket=s3_bucket_name,
        Prefix=s3_template_prefix,
        StartAfter=s3_template_prefix,
    )

    templates = s3_response.get("Contents", [])

    for template in templates:
        template_key = template["Key"]

        template_path_split = template_key.split(".tar.gz")
        if len(template_path_split) != 2:
            logger.warning("Skipping not .tar.gz object: %s", template_key)
            continue

        template_proton_name = os.path.basename(template_path_split[0])

        yield template_key, template_proton_name


@tracer.capture_method
def _create_proton_environment_template(
    template_proton_name: str, bucket_name: str, template_key: str
) -> Tuple[str, str]:

    get_proton_client().create_environment_template(name=template_proton_name)

    new_proton_env_template_version = (
        get_proton_client().create_environment_template_version(
            source={
                "s3": {
                    "bucket": bucket_name,
                    "key": template_key,
                }
            },
            templateName=template_proton_name,
            majorVersion="1",
        )
    )

    environment_template_version = new_proton_env_template_version[
        "environmentTemplateVersion"
    ]
    major_version = environment_template_version["majorVersion"]
    minor_version = environment_template_version["minorVersion"]

    return major_version, minor_version


@tracer.capture_method
def _wait_for_proton_environment_template_to_be_ready(
    context: LambdaContext,
    template_proton_name: str,
    template_major_version: str,
    template_minor_version: str,
) -> None:

    while context.get_remaining_time_in_millis() > REMAINING_TIME_THRESHOLD:

        logger.info("Waiting for template draft")

        if get_proton_client().get_environment_template_version(
            templateName=template_proton_name,
            majorVersion=template_major_version,
            minorVersion=template_minor_version,
        )["environmentTemplateVersion"]["status"] in ["DRAFT", "PUBLISHED"]:
            return

        time.sleep(5)

    logger.error("Lambda timeout margin exceeded, gracefully failing before shutdown.")
    raise TimeoutError(
        "Proton template version could not be created in DRAFT/PUBLISHED state before CFN Custom Resource timeout."
    )


@tracer.capture_method
def _create_or_update_proton_environment(
    template_proton_name: str,
    template_major_version: str,
    template_minor_version: str,
    codebuild_iam_role_arn: str,
) -> None:
    try:

        current_environment = get_proton_client().get_environment(
            name=template_proton_name
        )

        current_environment_template_name = current_environment["environment"][
            "templateName"
        ]
        if current_environment_template_name != template_proton_name:
            raise ValueError(
                f"Unexpected Proton Template '{current_environment_template_name}' found on Existing Environment. Expecting template: '{template_proton_name}'"
            )

        get_proton_client().update_environment(
            name=template_proton_name,
            templateMajorVersion=template_major_version,
            templateMinorVersion=template_minor_version,
            deploymentType="MINOR_VERSION",
            spec="{proton: EnvironmentSpec, spec: {a_number: 123}}",
            codebuildRoleArn=codebuild_iam_role_arn,
        )
    except get_proton_client().exceptions.ResourceNotFoundException:
        get_proton_client().create_environment(
            name=template_proton_name,
            templateName=template_proton_name,
            templateMajorVersion=template_major_version,
            templateMinorVersion=template_minor_version,
            spec="{proton: EnvironmentSpec, spec: {a_number: 123}}",
            codebuildRoleArn=codebuild_iam_role_arn,
        )


@tracer.capture_method
def create_proton_environment(event: Dict[str, Any], context: LambdaContext) -> None:
    if event["RequestType"] in [
        CustomResourceTypes.RequestTypes.CREATE.value,
        CustomResourceTypes.RequestTypes.UPDATE.value,
    ]:
        print(event)
        try:

            bucket_name = event["ResourceProperties"].get("TEMPLATE_S3_BUCKET_NAME")
            codebuild_iam_role_arn = event["ResourceProperties"].get(
                "CODE_BUILD_IAM_ROLE"
            )

            templates = _get_s3_proton_templates(
                s3_bucket_name=bucket_name,
                s3_template_path_prefix=event["ResourceProperties"].get(
                    "TEMPLATE_S3_KEY_PREFIX"
                ),
            )

            for template_key, template_proton_name in templates:

                major_version, minor_version = _create_proton_environment_template(
                    template_proton_name=template_proton_name,
                    bucket_name=bucket_name,
                    template_key=template_key,
                )

                _wait_for_proton_environment_template_to_be_ready(
                    context=context,
                    template_proton_name=template_proton_name,
                    template_major_version=major_version,
                    template_minor_version=minor_version,
                )

                get_proton_client().update_environment_template_version(
                    templateName=template_proton_name,
                    majorVersion=major_version,
                    minorVersion=minor_version,
                    status="PUBLISHED",
                )

                _create_or_update_proton_environment(
                    template_proton_name=template_proton_name,
                    template_major_version=major_version,
                    template_minor_version=minor_version,
                    codebuild_iam_role_arn=codebuild_iam_role_arn,
                )

        except ClientError as error:
            logger.error("Error while creating environment: %s", error)


@tracer.capture_method
def create_deployment_uuid(event: Dict[str, Any]) -> Dict[str, Any]:
    response = {}

    if event["RequestType"] == CustomResourceTypes.RequestTypes.CREATE.value:
        response["SolutionUUID"] = str(uuid.uuid4())

    return response


class CustomResourceTypes:
    class RequestTypes(Enum):
        CREATE = "Create"
        DELETE = "Delete"
        UPDATE = "Update"

    class ResourceTypes(Enum):
        CREATE_PROTON_ENVIRONMENT = "CreateProtonEnvironment"
        CREATE_DEPLOYMENT_UUID = "CreateDeploymentUUID"

    class StatusTypes(Enum):
        SUCCESS = "SUCCESS"
        FAILED = "FAILED"
