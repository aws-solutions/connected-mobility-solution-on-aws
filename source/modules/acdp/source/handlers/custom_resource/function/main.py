# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import io
import json
import mimetypes
import os
import posixpath
import re
import uuid
import zipfile
from enum import Enum
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Dict

# Third Party Libraries
import requests
import yaml
from yaml.loader import SafeLoader

# AWS Libraries
import boto3
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.config import Config

if TYPE_CHECKING:
    # Third Party Libraries
    from mypy_boto3_s3.client import S3Client
    from mypy_boto3_s3.type_defs import CopySourceTypeDef
else:
    CopySourceTypeDef = object
    S3Client = object

tracer = Tracer()
logger = Logger()

REMAINING_TIME_THRESHOLD = 10000  # milliseconds


@lru_cache(maxsize=128)
def get_s3_client() -> S3Client:
    return boto3.client(
        "s3", config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"])
    )


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    response = {"Status": CustomResourceTypes.StatusTypes.SUCCESS.value, "Data": {}}
    reason = f"See the details in CloudWatch Log Stream: {context.log_stream_name}"

    try:

        match event["ResourceProperties"]["Resource"]:
            case CustomResourceTypes.ResourceTypes.CREATE_DEPLOYMENT_UUID.value:
                response["Data"] = create_deployment_uuid(event)
            case CustomResourceTypes.ResourceTypes.CREATE_AND_UPLOAD_DEFAULT_USERS_AND_GROUPS.value:
                create_and_upload_default_users_and_groups(event)
            case CustomResourceTypes.ResourceTypes.COPY_S3_OBJECT.value:
                response["Data"] = copy_s3_object_from_source_to_destination_bucket(
                    event
                )
            case CustomResourceTypes.ResourceTypes.EXTRACT_S3_ZIP_TO_TARGET_BUCKET.value:
                extract_s3_zip_object_from_source_to_destination_bucket(event)
            case CustomResourceTypes.ResourceTypes.VALIDATE_MULTI_ACCOUNT_PARAMETERS.value:
                validate_multi_account_parameters(event)
            case _:
                raise KeyError(
                    f"No Custom Resource Type: {event['ResourceProperties']['Resource']}"
                )

    except Exception as exception:  # pylint: disable=broad-exception-caught
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
def create_deployment_uuid(event: Dict[str, Any]) -> Dict[str, Any]:
    response = {}

    if event["RequestType"] == CustomResourceTypes.RequestTypes.CREATE.value:
        response["SolutionUUID"] = str(uuid.uuid4())

    return response


@tracer.capture_method
def create_and_upload_default_users_and_groups(event: Dict[str, Any]) -> None:
    if event["RequestType"] in [
        CustomResourceTypes.RequestTypes.CREATE.value,
        CustomResourceTypes.RequestTypes.UPDATE.value,
    ]:
        destination_bucket = event["ResourceProperties"]["DestinationBucket"]
        destination_key_prefix = event["ResourceProperties"]["DestinationKeyPrefix"]
        environment = event["ResourceProperties"]["CustomEnvironment"]

        # Custom constructor to replace environment variables (denoted by !ENV tag) with value from supplied environment dict
        def env_constructor(loader: SafeLoader, node: yaml.Node) -> str:
            value = str(loader.construct_scalar(node))  # type: ignore[arg-type]
            return str(environment.get(value, ""))

        yaml.add_constructor(tag="!ENV", constructor=env_constructor, Loader=SafeLoader)

        def update_yaml_env_variables_to_s3(
            input_path: str,
        ) -> bool:
            try:
                failure_occurred = False
                # Load and process the YAML file (which might have yaml subfiles inside)
                consistent_relative_path = os.path.join(
                    os.path.dirname(__file__), input_path
                )
                with open(
                    consistent_relative_path, "r", encoding="utf-8"
                ) as yaml_file_stream:
                    updated_yamls = list(
                        yaml.load_all(yaml_file_stream, Loader=SafeLoader)
                    )

                # For each yaml subfile, convert to string, and upload to the appropriate S3 key
                s3_client = boto3.client("s3")
                for yaml_doc in updated_yamls:
                    namespace = yaml_doc.get("metadata").get("namespace").lower()
                    kind = yaml_doc.get("kind").lower()
                    name = yaml_doc.get("metadata").get("name").lower()
                    full_s3_key = f"{destination_key_prefix}/{namespace}/{kind}/{name}/catalog-info.yaml"

                    yaml_as_string = yaml.dump(
                        yaml_doc,
                        Dumper=yaml.SafeDumper,
                        default_flow_style=False,
                    )

                    s3_client.put_object(
                        Bucket=destination_bucket,
                        Key=full_s3_key,
                        Body=yaml_as_string,
                        ContentType="application/x-yaml",
                    )
            except Exception as exception:  # pylint: disable=broad-exception-caught
                # Individually recatch and throw exceptions in the loop, so that failure on one file will still allow other file attempts to continue
                logger.error(
                    "CustomResource CreateAndUploadDefaultUsersAndGroups error: %s",
                    str(exception),
                    exc_info=True,
                )
                failure_occurred = True
            return failure_occurred

        users_failure = update_yaml_env_variables_to_s3("lib/default_admin_user.yaml")
        groups_failure = update_yaml_env_variables_to_s3("lib/default_groups.yaml")

        if users_failure or groups_failure:
            raise Exception(  # pylint: disable=broad-exception-raised
                "One or more yaml files failed to parse and upload to the destination S3 bucket. See prior CloudWatch logs for individual failures."
            )


@tracer.capture_method
def copy_s3_object_from_source_to_destination_bucket(
    event: Dict[str, Any]
) -> Dict[str, Any]:
    response = {}

    if event["RequestType"] in [
        CustomResourceTypes.RequestTypes.CREATE.value,
        CustomResourceTypes.RequestTypes.UPDATE.value,
    ]:
        copy_source: CopySourceTypeDef = {
            "Bucket": event["ResourceProperties"]["SourceBucket"],
            "Key": event["ResourceProperties"]["SourceKey"],
        }
        destination_bucket: str = event["ResourceProperties"]["DestinationBucket"]

        destination_key: str = event["ResourceProperties"]["DestinationKey"]

        get_s3_client().copy(copy_source, destination_bucket, destination_key)

        response["DestinationBucket"] = destination_bucket
        response["DestinationKey"] = destination_key

    return response


@tracer.capture_method
def extract_s3_zip_object_from_source_to_destination_bucket(
    event: Dict[str, Any]
) -> None:
    if event["RequestType"] in [
        CustomResourceTypes.RequestTypes.CREATE.value,
        CustomResourceTypes.RequestTypes.UPDATE.value,
    ]:
        source_bucket_name = event["ResourceProperties"]["SourceBucket"]
        source_bucket_key = event["ResourceProperties"]["SourceZipKey"]
        destination_bucket_name = event["ResourceProperties"]["DestinationBucket"]
        destination_bucket_key = event["ResourceProperties"]["DestinationKeyPrefix"]

        zip_obj = get_s3_client().get_object(
            Bucket=source_bucket_name, Key=source_bucket_key
        )
        buffer = io.BytesIO(zip_obj["Body"].read())

        with zipfile.ZipFile(buffer, mode="r") as z:
            for file_name in z.namelist():
                file_info = z.getinfo(file_name)
                if not file_info.is_dir():
                    content_type = (
                        mimetypes.guess_type(file_name)[0] or "application/octet-stream"
                    )
                    with z.open(file_name) as file:
                        get_s3_client().upload_fileobj(
                            file,
                            destination_bucket_name,
                            posixpath.join(destination_bucket_key, file_name),
                            ExtraArgs={"ContentType": content_type},
                        )


@tracer.capture_method
def validate_multi_account_parameters(event: Dict[str, Any]) -> None:

    if event["RequestType"] in [
        CustomResourceTypes.RequestTypes.CREATE.value,
        CustomResourceTypes.RequestTypes.UPDATE.value,
    ]:
        if event["ResourceProperties"]["EnableMultiAccountDeployment"] == "true" and (
            not (
                re.match(
                    ArnPatterns.ACCOUNT_ID.value,
                    event["ResourceProperties"]["OrgsManagementAwsAccountId"],
                )
                and re.match(
                    ArnPatterns.REGION.value,
                    event["ResourceProperties"]["OrgsManagementAccountRegion"],
                )
            )
        ):
            raise ValueError(
                "Multi-Account deployment feature is enabled, Provide valid AWS Account ID and AWS Region"
            )


class ArnPatterns(Enum):
    ACCOUNT_ID = r"^(?!null$)\d{12}$"
    REGION = r"^(?!null$)(us|eu|ap|sa|ca|me|af|il)-(north|south|east|west|central)-(1|2|3|4)$"


class CustomResourceTypes:
    class RequestTypes(Enum):
        CREATE = "Create"
        DELETE = "Delete"
        UPDATE = "Update"

    class ResourceTypes(Enum):
        CREATE_DEPLOYMENT_UUID = "CreateDeploymentUUID"
        CREATE_AND_UPLOAD_DEFAULT_USERS_AND_GROUPS = (
            "CreateAndUploadDefaultUsersAndGroups"
        )
        COPY_S3_OBJECT = "CopyS3Object"
        EXTRACT_S3_ZIP_TO_TARGET_BUCKET = "ExtractS3ZipToTargetBucket"
        VALIDATE_MULTI_ACCOUNT_PARAMETERS = "ValidateMultiAccountParameters"

    class StatusTypes(Enum):
        SUCCESS = "SUCCESS"
        FAILED = "FAILED"
