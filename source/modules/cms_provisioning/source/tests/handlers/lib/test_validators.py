# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0


# Third Party Libraries
import pytest

# Connected Mobility Solution on AWS
from ....handlers.provisioning.function.lib.certificate_status_enum import (
    CertificateStatus,
)
from ....handlers.provisioning.function.lib.validators import (
    sanitize_vin,
    validate_certificate_status,
)


@pytest.mark.parametrize("vin", [123456, ["ABCD", "1234"], True])
def test_sanitize_vin_wrong_type(vin: str) -> None:
    with pytest.raises(Exception):
        sanitize_vin(vin=vin)


def test_sanitize_vin_capitalizes_input() -> None:
    vin_lowercase = "abcdefghij1234567"
    sanitized_vin = sanitize_vin(vin=vin_lowercase)
    assert sanitized_vin == vin_lowercase.upper()


def test_sanitize_vin_removes_non_alphanumeric_characters() -> None:
    vin_non_alphanumeric_chars = "abcdefghij 1234:56\n7.."
    sanitized_vin = sanitize_vin(vin=vin_non_alphanumeric_chars)
    assert sanitized_vin == "ABCDEFGHIJ1234567"


def test_validate_certificate_status_success() -> None:
    for status in CertificateStatus:
        validate_certificate_status(None, None, status.value)  # type: ignore[arg-type]


def test_validate_certificate_status_fail() -> None:
    with pytest.raises(ValueError):
        validate_certificate_status(None, None, "invalid certificate status")  # type: ignore[arg-type]
