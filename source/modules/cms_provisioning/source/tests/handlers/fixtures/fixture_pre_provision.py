# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
import os
from typing import Any, Dict

# Third Party Libraries
import pytest

# Connected Mobility Solution on AWS
from ....handlers.provisioning.function.lib.dynamo_schema import AuthorizedVehicle


@pytest.fixture(name="pre_provision_event")
def fixture_pre_provision_event() -> Dict[str, Any]:
    # There are other fields but they are not important for our tests: https://docs.aws.amazon.com/iot/latest/developerguide/pre-provisioning-hook.html
    return {
        "certificateId": os.environ["TEST_CERTIFICATE_ID"],
        "parameters": {"vin": os.environ["TEST_VIN"]},
    }


@pytest.fixture(name="pre_provision_event_invalid")
def fixture_pre_provision_event_invalid() -> Dict[str, Any]:
    return {
        "claimCertificateId": "123456789ClaimCertificatedId123456789",
        "certificateId": "123456789CertificatedId123456789",
        "certificatePem": "TypicallyVeryLongCertificatePemString",
        "templateArn": "arn:aws:iot:us-east-1:123456789:provisioningtemplate/cms-vehicle-provisioning-template",
        "clientId": "test-b46aa22b-d9fd-4c94-a641-e796adddf91c",
        "parameters": {},  # Missing vin
    }


@pytest.fixture(name="authorized_vehicle_allowed")
def fixture_authorized_vehicle_allowed() -> AuthorizedVehicle:
    return AuthorizedVehicle(
        vin=os.environ["TEST_VIN"],
        make="test_make",
        model="test_model",
        year="test_year",
        allow_provisioning=True,
    )
