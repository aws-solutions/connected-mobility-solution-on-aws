# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json
import os
from functools import lru_cache
from typing import TYPE_CHECKING, Any, Dict

# Third Party Libraries
import humps  # NOTE: not yet supported on Python 3.11

# AWS Libraries
import boto3
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.config import Config

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
def handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    response = {"status": "FAILURE"}

    operations = {
        "publish": publish_message,
    }

    try:
        operations[event["info"]["fieldName"]](humps.decamelize(event["arguments"]))
        response["status"] = "SUCCESS"
    except KeyError:
        logger.error("KeyError while publishing the message", exc_info=True)
        response["message"] = "KeyError while publishing the message"
    except Exception:  # pylint: disable=broad-exception-caught
        logger.error(
            msg=f"Error occured while publishing the message: {event['arguments']} to topic: {os.environ['ALERTS_SNS_TOPIC_ARN']}",
            exc_info=True,
        )
        response[
            "message"
        ] = f"Error occured while publishing the message: {event['arguments']}"

    return response


@tracer.capture_method
def publish_message(message: Dict[str, Any]) -> None:
    get_sns_client().publish(
        Message=json.dumps(message),
        TopicArn=os.environ["ALERTS_SNS_TOPIC_ARN"],
    )
