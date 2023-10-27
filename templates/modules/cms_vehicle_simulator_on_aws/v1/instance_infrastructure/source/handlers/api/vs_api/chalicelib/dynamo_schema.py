# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from abc import ABCMeta
from typing import Any, List, Optional

# Third Party Libraries
from attrs import define, field
from attrs.validators import deep_iterable, instance_of, matches_re, optional
from cattrs import global_converter, override, register_unstructure_hook
from cattrs.gen import make_dict_unstructure_fn


@define
class IDynamoDBItem(metaclass=ABCMeta):
    pass


@define(frozen=True, auto_attribs=True)
class DeviceTypeAttribute(IDynamoDBItem):
    name: str = field(validator=[instance_of(str), matches_re("[A-Za-z0-9-_ ]*")])
    type: str = field(validator=[instance_of(str), matches_re("[A-Za-z0-9-_ ]*")])
    charSet: Optional[str] = field(  # pylint: disable=invalid-name
        default=None, validator=[optional(instance_of(str))]
    )
    length: Optional[int] = field(default=None, validator=[optional(instance_of(int))])
    default: Optional[Any] = field(default=None)
    static: Optional[bool] = field(
        default=None, validator=[optional(instance_of(bool))]
    )
    tsformat: Optional[str] = field(
        default=None, validator=[optional(instance_of(str))]
    )
    precision: Optional[int] = field(
        default=None, validator=[optional(instance_of(int))]
    )
    min: Optional[float] = field(default=None, validator=[optional(instance_of(float))])
    max: Optional[float] = field(default=None, validator=[optional(instance_of(float))])
    lat: Optional[float] = field(default=None, validator=[optional(instance_of(float))])
    long: Optional[float] = field(
        default=None, validator=[optional(instance_of(float))]
    )
    radius: Optional[float] = field(
        default=None, validator=[optional(instance_of(float))]
    )
    arr: Optional[List[str]] = field(
        default=None, validator=[optional(deep_iterable(instance_of(str)))]  # type: ignore[arg-type]
    )
    object: "Optional[DeviceTypeAttribute]" = field(default=None)
    payload: "Optional[List[DeviceTypeAttribute]]" = field(default=None)


register_unstructure_hook(
    DeviceTypeAttribute,
    make_dict_unstructure_fn(
        DeviceTypeAttribute,
        global_converter,
        _cattrs_omit_if_default=True,
        b=override(omit_if_default=False),
    ),
)


@define(frozen=True, auto_attribs=True)
class DeviceTypeTemplate(IDynamoDBItem):
    template_id: str = field(validator=[instance_of(str)])
    payload: List[DeviceTypeAttribute] = field(
        validator=[deep_iterable(instance_of(DeviceTypeAttribute))]
    )
    created_datetime: Optional[str] = field(
        default=None, validator=[optional(instance_of(str))]
    )
    updated_datetime: Optional[str] = field(
        default=None, validator=[optional(instance_of(str))]
    )


register_unstructure_hook(
    DeviceTypeTemplate,
    make_dict_unstructure_fn(
        DeviceTypeTemplate,
        global_converter,
        _cattrs_omit_if_default=True,
    ),
)


@define(frozen=True, auto_attribs=True)
class DeviceType(IDynamoDBItem):
    type_id: str = field(validator=[instance_of(str)])
    name: str = field(validator=[instance_of(str), matches_re("[A-Za-z0-9-_ ]*")])
    topic: str = field(validator=[instance_of(str), matches_re("[A-Za-z0-9-_ /]*")])
    payload: List[DeviceTypeAttribute] = field(
        validator=[deep_iterable(instance_of(DeviceTypeAttribute))]
    )
    created_datetime: Optional[str] = field(
        default=None, validator=[optional(instance_of(str))]
    )
    updated_datetime: Optional[str] = field(
        default=None, validator=[optional(instance_of(str))]
    )


register_unstructure_hook(
    DeviceType,
    make_dict_unstructure_fn(
        DeviceType,
        global_converter,
        _cattrs_omit_if_default=True,
    ),
)


@define(frozen=True, auto_attribs=True)
class Device(IDynamoDBItem):
    type_id: str = field(validator=[instance_of(str), matches_re("[A-Za-z0-9-_ ]*")])
    name: str = field(validator=[instance_of(str), matches_re("[A-Za-z0-9-_ ]*")])
    amount: str = field(validator=[instance_of(str)])


@define(frozen=True, auto_attribs=True)
class Simulation(IDynamoDBItem):
    sim_id: str = field(validator=[instance_of(str), matches_re("[A-Za-z0-9-_ ]*")])
    name: str = field(validator=[instance_of(str), matches_re("[A-Za-z0-9-_ ]*")])
    stage: str = field(validator=[instance_of(str), matches_re("[A-Za-z0-9-_ ]*")])
    duration: int = field(validator=[instance_of(int)])
    interval: int = field(validator=[instance_of(int)])
    devices: List[Device] = field(validator=[deep_iterable(instance_of(Device))])
    runs: Optional[int] = field(default=None, validator=[optional(instance_of(int))])
    last_run: Optional[str] = field(
        default=None, validator=[optional(instance_of(str))]
    )
    current_run_arn: Optional[str] = field(
        default=None, validator=[optional(instance_of(str))]
    )
    created_datetime: Optional[str] = field(
        default=None, validator=[optional(instance_of(str))]
    )
    updated_datetime: Optional[str] = field(
        default=None, validator=[optional(instance_of(str))]
    )
    checked: Optional[bool] = field(
        default=None, validator=[optional(instance_of(bool))]
    )


register_unstructure_hook(
    Simulation,
    make_dict_unstructure_fn(
        Simulation,
        global_converter,
        _cattrs_omit_if_default=True,
    ),
)


@define(frozen=True, auto_attribs=True)
class UpdateSimulationsRequest:
    action: str = field(validator=[instance_of(str)])
    simulations: List[Simulation] = field(
        validator=[deep_iterable(instance_of(Simulation))]
    )
