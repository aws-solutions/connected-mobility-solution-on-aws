# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json
import os
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Dict, List

# Third Party Libraries
import requests
from opensearchpy import AWSV4SignerAuth, OpenSearch, RequestsHttpConnection
from tenacity import retry, retry_if_exception_type, stop_after_delay, wait_fixed

# AWS Libraries
import boto3
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.config import Config

# CMS Common Library
from cms_common.enums.custom_resource import (
    CustomResourceRequestType,
    CustomResourceStatusType,
)

# Connected Mobility Solution on AWS
from .lib.custom_resource_type_enum import CustomResourceFunctionType
from .lib.pipeline import create_predictive_maintenance_pipeline

if TYPE_CHECKING:
    # Third Party Libraries
    from mypy_boto3_bedrock_agent import AgentsforBedrockClient
    from mypy_boto3_ec2 import EC2Client
    from mypy_boto3_efs import EFSClient
    from mypy_boto3_opensearchserverless.client import OpenSearchServiceServerlessClient
    from mypy_boto3_s3 import S3Client
else:
    OpenSearchServiceServerlessClient = object
    AgentsforBedrockClient = object
    S3Client = object
    EFSClient = object
    EC2Client = object

tracer = Tracer()
logger = Logger()


@lru_cache(maxsize=1)
def get_opensearchserverless_client() -> OpenSearchServiceServerlessClient:
    return boto3.client(
        "opensearchserverless",
        config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"]),
    )


@lru_cache(maxsize=1)
def get_s3_client() -> S3Client:
    return boto3.client(
        "s3", config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"])
    )


@lru_cache(maxsize=1)
def get_bedrock_agent_client() -> AgentsforBedrockClient:
    return boto3.client(
        "bedrock-agent", config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"])
    )


@lru_cache(maxsize=1)
def get_efs_client() -> EFSClient:
    return boto3.client(
        "efs", config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"])
    )


@lru_cache(maxsize=1)
def get_ec2_client() -> EC2Client:
    return boto3.client(
        "ec2", config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"])
    )


def get_oss_client(collection_id: str) -> OpenSearch:
    credentials = boto3.Session().get_credentials()
    awsauth = AWSV4SignerAuth(credentials, os.environ["AWS_REGION"], "aoss")
    host_url = f"{collection_id}.{os.environ['AWS_REGION']}.aoss.amazonaws.com"

    oss_client = OpenSearch(
        hosts=[{"host": host_url, "port": 443}],
        http_auth=awsauth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection,
        timeout=300,
    )
    return oss_client


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    response = {"Status": CustomResourceStatusType.SUCCESS.value, "Data": {}}
    reason = f"See the details in CloudWatch Log Stream: {context.log_stream_name}"

    try:
        match event["ResourceProperties"]["Resource"]:
            case CustomResourceFunctionType.MANAGE_AOSS_VECTOR_INDEX.value:
                response["Data"] = manage_aoss_vector_index(event)
            case CustomResourceFunctionType.GET_AOSS_VPC_ENDPOINT_ID.value:
                response["Data"] = get_aoss_vpc_endpoint_id(event)
            case CustomResourceFunctionType.INGEST_BEDROCK_DATA_SOURCE.value:
                response["Data"] = ingest_bedrock_data_source(event)
            case CustomResourceFunctionType.CREATE_AND_UPLOAD_SAGEMAKER_PIPELINE_DEFINITION.value:
                response["Data"] = create_and_upload_sagemaker_pipeline_definition(
                    event
                )
            case CustomResourceFunctionType.DELETE_SAGEMAKER_DOMAIN_EFS.value:
                response["Data"] = delete_sagemaker_domain_efs(event)
            case _:
                raise KeyError(
                    f"No Custom Resource Type: {event['ResourceProperties']['Resource']}"
                )

    except Exception as exception:  # pylint: disable=W0703
        # Wrap all exceptions so CloudFormation doesn't hang
        logger.error("CustomResource error: %s", str(exception), exc_info=True)
        response["Status"] = CustomResourceStatusType.FAILED.value
        reason = f"{str(exception)} ... {reason}"

    if bool(event["ResourceProperties"].get("DoNotSendCFResponse", False)) is not True:
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
def manage_aoss_vector_index(event: Dict[str, Any]) -> None:
    collection_id = event["ResourceProperties"]["AOSSCollectionId"]
    if event["RequestType"] == CustomResourceRequestType.CREATE.value:
        get_oss_client(collection_id=collection_id).indices.create(
            index=event["ResourceProperties"]["VectorIndexName"],
            body=event["ResourceProperties"]["VectorIndexConfigJsonStr"],
        )
    elif event["RequestType"] == CustomResourceRequestType.DELETE.value:
        get_oss_client(collection_id=collection_id).indices.delete(
            index=event["ResourceProperties"]["VectorIndexName"]
        )


@tracer.capture_method
def get_aoss_vpc_endpoint_id(event: Dict[str, Any]) -> Dict[str, Any]:
    response = {}
    if event["RequestType"] in [
        CustomResourceRequestType.CREATE.value,
        CustomResourceRequestType.UPDATE.value,
    ]:
        vpc_endpoints = get_opensearchserverless_client().list_vpc_endpoints()
        for vpc_endpoint in vpc_endpoints["vpcEndpointSummaries"]:
            if vpc_endpoint["name"] == event["ResourceProperties"]["VpcEndpointName"]:
                response["vpce_id"] = vpc_endpoint["id"]
    return response


@tracer.capture_method
def ingest_bedrock_data_source(event: Dict[str, Any]) -> None:
    if event["RequestType"] in [
        CustomResourceRequestType.CREATE.value,
        CustomResourceRequestType.UPDATE.value,
    ]:
        get_bedrock_agent_client().start_ingestion_job(
            dataSourceId=event["ResourceProperties"]["DataSourceId"],
            description=f'{event["ResourceProperties"]["DataSourceId"]} - ingest data source',
            knowledgeBaseId=event["ResourceProperties"]["KnowledgeBaseId"],
        )


@tracer.capture_method
def create_and_upload_sagemaker_pipeline_definition(event: Dict[str, Any]) -> None:
    if event["RequestType"] in [
        CustomResourceRequestType.CREATE.value,
        CustomResourceRequestType.UPDATE.value,
    ]:
        pipeline = create_predictive_maintenance_pipeline(
            pipeline_name=event["ResourceProperties"]["PipelineName"],
            pipeline_role_arn=event["ResourceProperties"]["PipelineRoleArn"],
            pipeline_assets_bucket_name=event["ResourceProperties"][
                "PipelineAssetsBucketName"
            ],
            deploy_model_function_arn=event["ResourceProperties"][
                "PipelineDeployModelLambdaArn"
            ],
            endpoint_name=event["ResourceProperties"]["SageMakerModelEndpointName"],
            resource_name_suffix=event["ResourceProperties"]["ResourceNameSuffix"],
        )

        get_s3_client().put_object(
            Body=pipeline.definition().encode("utf-8"),
            Bucket=event["ResourceProperties"]["PipelineAssetsBucketName"],
            Key=event["ResourceProperties"]["PipelineDefinitionS3Key"],
            ContentType="application/json",
        )


@tracer.capture_method
def delete_security_groups(security_group_ids: List[str]) -> None:
    for security_group_id in security_group_ids:
        security_group = get_ec2_client().describe_security_groups(
            GroupIds=[security_group_id]
        )["SecurityGroups"][0]

        try:
            if security_group["IpPermissions"]:
                get_ec2_client().revoke_security_group_ingress(
                    GroupId=security_group_id,
                    IpPermissions=security_group["IpPermissions"],
                )
            logger.info(f"Ingress rule revoked for security group {security_group_id}.")
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.info(
                f"Ingress rule revoking failed with {e} for security group {security_group_id}"
            )

        try:
            if security_group["IpPermissionsEgress"]:
                get_ec2_client().revoke_security_group_egress(
                    GroupId=security_group_id,
                    IpPermissions=security_group["IpPermissionsEgress"],
                )
            logger.info(f"Engress rule revoked for security group {security_group_id}.")
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.info(
                f"Engress rule revoking failed with {e} for security group {security_group_id}"
            )

    for security_group_id in security_group_ids:
        get_ec2_client().delete_security_group(GroupId=security_group_id)
        logger.info(f"Deleted security group: {security_group_id}")


@tracer.capture_method
def get_security_groups_for_mount_targets(mount_target_id: str) -> List[str]:
    security_group_ids = set()

    inbound_security_group_ids = get_efs_client().describe_mount_target_security_groups(
        MountTargetId=mount_target_id
    )["SecurityGroups"]
    security_group_ids.update(inbound_security_group_ids)

    for inbound_security_group_id in inbound_security_group_ids:
        security_group = get_ec2_client().describe_security_groups(
            GroupIds=[inbound_security_group_id]
        )["SecurityGroups"][0]
        ip_permissions = security_group["IpPermissions"]
        for ip_permission in ip_permissions:
            outbound_security_groups = [
                user_id_group_pair["GroupId"]
                for user_id_group_pair in ip_permission["UserIdGroupPairs"]
            ]
            security_group_ids.update(outbound_security_groups)

    return list(security_group_ids)


@tracer.capture_method
def delete_sagemaker_domain_efs(event: Dict[str, Any]) -> None:
    if event["RequestType"] in [
        CustomResourceRequestType.DELETE.value,
    ]:
        home_efs_file_system_id = event["ResourceProperties"]["HomeEfsFileSystemId"]

        security_groups_to_delete = set()

        mount_targets = get_efs_client().describe_mount_targets(
            FileSystemId=home_efs_file_system_id,
        )

        for mount_target in mount_targets["MountTargets"]:
            mount_target_id = mount_target["MountTargetId"]
            mount_target_security_groups = get_security_groups_for_mount_targets(
                mount_target_id=mount_target_id
            )
            security_groups_to_delete.update(mount_target_security_groups)

            get_efs_client().delete_mount_target(
                MountTargetId=mount_target_id,
            )

        @retry(
            retry=retry_if_exception_type(AssertionError),
            stop=stop_after_delay(30),
            wait=wait_fixed(5),
        )
        def wait_for_deleting_mount_targets() -> None:
            num_mount_targets = len(
                get_efs_client().describe_mount_targets(
                    FileSystemId=home_efs_file_system_id
                )["MountTargets"]
            )
            logger.info(
                f"Waiting to delete mount targets. Number of mount targets: {num_mount_targets}"
            )

            assert num_mount_targets == 0  # nosec

        wait_for_deleting_mount_targets()
        delete_security_groups(security_group_ids=list(security_groups_to_delete))
        get_efs_client().delete_file_system(
            FileSystemId=home_efs_file_system_id,
        )
