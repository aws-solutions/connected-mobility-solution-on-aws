# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from abc import ABCMeta
from typing import Any, Dict, TypeVar

# Third Party Libraries
from attrs import define, field
from attrs.validators import instance_of

# AWS Libraries
from boto3.dynamodb.types import TypeDeserializer


@define
class IDynamoDBItem(metaclass=ABCMeta):
    pass


DynamoDBItem = TypeVar("DynamoDBItem", bound=IDynamoDBItem)


@define(frozen=True, auto_attribs=True)
class DynamoDBDetails:
    new_image: Dict[str, Any] = field(validator=[instance_of(dict)])


@define(frozen=True, auto_attribs=True)
class StreamRecord(IDynamoDBItem):
    dynamodb: DynamoDBDetails = field(validator=[instance_of(DynamoDBDetails)])


def from_ddb_stream_record(record_dict: Dict[str, Any]) -> StreamRecord:
    deserializer = TypeDeserializer()
    dynamodb_details = record_dict.get("dynamodb", {})

    # Deserialize NewImage
    new_image = dynamodb_details.get("NewImage")
    deserialized_new_image = {}
    for key, value in new_image.items():
        deserialized_new_image[key] = deserializer.deserialize(value)

    return StreamRecord(
        dynamodb=DynamoDBDetails(
            new_image=deserialized_new_image,
        ),
    )
