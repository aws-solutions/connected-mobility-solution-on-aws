# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Dict

# AWS Libraries
import boto3
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.config import Config

# Connected Mobility Solution on AWS
from .lib.dynamo_stream_schema import from_ddb_stream_record

if TYPE_CHECKING:
    # Third Party Libraries
    from mypy_boto3_sns.client import SNSClient
else:
    SNSClient = object


tracer = Tracer()
logger = Logger()


@lru_cache(maxsize=128)
def get_sns_client() -> SNSClient:
    return boto3.client(
        "sns", config=Config(user_agent_extra=os.environ["USER_AGENT_STRING"])
    )


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: Dict[str, Any], context: LambdaContext) -> None:
    try:
        for record in event["Records"]:
            sanitized_record = from_ddb_stream_record(record)
            notification = sanitized_record.dynamodb.new_image
            topic = get_sns_client().create_topic(  # idempotent
                Name=notification["topic"],
                Tags=[{"Key": "AlertsUUID", "Value": os.environ["DEPLOYMENT_UUID"]}],
            )

            get_sns_client().publish(
                Message=notification["message"],
                TopicArn=topic["TopicArn"],
            )
    except Exception as err:
        logger.error(msg="Error while trying to publish notification", exc_info=True)
        raise err
