# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
from typing import Any, Dict

# Third Party Libraries
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

# Connected Mobility Solution on AWS
from .lib.dynamo_crud import DynHelpers
from .lib.sqs_record_schema import from_sqs_record_dict

tracer = Tracer()
logger = Logger()


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: Dict[str, Any], context: LambdaContext) -> None:
    try:
        records = event["Records"]
        for record in records:
            sanitized_record = from_sqs_record_dict(record)
            DynHelpers.put_item(
                os.environ["NOTIFICATIONS_TABLE_NAME"],
                item={
                    "topic": f"{os.environ['SNS_TOPIC_PREFIX']}-{sanitized_record.body.message.alarm_type}-{sanitized_record.body.message.vin}",
                    "message": sanitized_record.body.message.message,
                    "read": False,
                },
            )
    except Exception as err:  # pylint: disable=broad-exception-caught
        logger.error("Error encountered while processing message", exc_info=True)
        raise err
