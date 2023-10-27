# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from abc import ABCMeta
from typing import Any, Dict, Mapping, Type, TypeVar

# Third Party Libraries
import cattrs
from attrs import asdict, define, field, fields
from attrs.validators import instance_of
from boto3.dynamodb.types import TypeDeserializer, TypeSerializer

# Connected Mobility Solution on AWS
from .validators import sanitize_vin, validate_certificate_status


@define
class IDynamoDBItem(metaclass=ABCMeta):
    pass


DynamoDBItem = TypeVar("DynamoDBItem", bound=IDynamoDBItem)


@define(frozen=True, auto_attribs=True)
class AuthorizedVehicle(IDynamoDBItem):
    vin: str = field(converter=sanitize_vin, validator=[instance_of(str)])
    make: str = field(validator=[instance_of(str)])
    model: str = field(validator=[instance_of(str)])
    year: str = field(validator=[instance_of(str)])
    allow_provisioning: bool = field(validator=[instance_of(bool)])


@define(frozen=True, auto_attribs=True)
class ProvisionedVehicle(IDynamoDBItem):
    vin: str = field(converter=sanitize_vin, validator=[instance_of(str)])
    certificate_id: str = field(validator=[instance_of(str)])
    make: str = field(validator=[instance_of(str)])
    model: str = field(validator=[instance_of(str)])
    year: str = field(validator=[instance_of(str)])
    region: str = field(validator=[instance_of(str)])
    thing_name: str = field(validator=[instance_of(str)])
    certificate_status: str = field(
        validator=[instance_of(str), validate_certificate_status]
    )
    has_vehicle_connected_once: bool = field(validator=[instance_of(bool)])


def from_ddb_item(cls: Type[DynamoDBItem], ddb_item: Dict[str, Any]) -> DynamoDBItem:
    deserializer = TypeDeserializer()
    dataclass_as_dict = {}

    # The following ignore is necessary due to issues caused by mypy v1.6
    for data_field in fields(cls):  # type: ignore[misc]
        dataclass_as_dict[data_field.name] = deserializer.deserialize(
            ddb_item.get(data_field.name, None)
        )
    return cattrs.structure(dataclass_as_dict, cls)


def to_ddb_item(obj: DynamoDBItem) -> Mapping[str, Any]:
    serializer = TypeSerializer()

    dataclass_as_dict = asdict(obj)
    ddb_item = serializer.serialize(dataclass_as_dict)["M"]
    return ddb_item
