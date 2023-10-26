# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import json
from typing import Any, Dict, Optional

# Third Party Libraries
from attrs import define, field
from attrs.validators import instance_of, optional


@define(frozen=True, auto_attribs=True)
class AlertMessage:
    vin: str = field(validator=[instance_of(str)])
    message: str = field(validator=[instance_of(str)])
    alarm_type: str = field(validator=[instance_of(str)])


@define(frozen=True, auto_attribs=True)
class MessageBody:
    message: AlertMessage = field(validator=[instance_of(AlertMessage)])


@define(frozen=True, auto_attribs=True)
class SQSRecord:
    body: MessageBody = field(validator=[instance_of(MessageBody)])
    message_attributes: Optional[Dict[str, str]] = field(
        validator=[optional(instance_of(dict))], default=None
    )


def from_sqs_record_dict(record_dict: Dict[str, Any]) -> SQSRecord:
    decoded_json_body_message = json.loads(
        json.loads(record_dict.get("body")).get("Message")  # type: ignore[arg-type]
    )

    return SQSRecord(
        body=MessageBody(
            message=AlertMessage(
                vin=decoded_json_body_message.get("vin"),
                message=decoded_json_body_message.get("message"),
                alarm_type=decoded_json_body_message.get("alarm_type"),
            )
        ),
        message_attributes=record_dict.get("messageAttributes", None),
    )
