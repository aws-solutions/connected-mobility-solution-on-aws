# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import re

# Third Party Libraries
from attrs import Attribute

# Connected Mobility Solution on AWS
from .certificate_status_enum import CertificateStatus

##### Validators - Verify input and dataclass fields


def validate_certificate_status(_: object, __: "Attribute[str]", value: str) -> None:
    valid_certificate_statuses = set(status.value for status in CertificateStatus)
    if value not in valid_certificate_statuses:
        raise ValueError(
            f"Invalid certificate status: {value}. Should be one of {valid_certificate_statuses}"
        )


##### Sanitizers - Transform input and dataclass fields


def sanitize_vin(vin: str) -> str:
    # remove characters that are not alphanumeric
    sanitized_vin = re.sub(r"[\W_]+", "", vin)
    # capitalize vin
    sanitized_vin = sanitized_vin.upper()
    return sanitized_vin
