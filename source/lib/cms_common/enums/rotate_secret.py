# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from enum import Enum


class RotateSecretStep(Enum):
    """Enum of secret rotation steps"""

    CREATE_SECRET = "createSecret"  # nosec
    SET_SECRET = "setSecret"  # nosec
    TEST_SECRET = "testSecret"  # nosec
    FINISH_SECRET = "finishSecret"  # nosec


class SecretStatus(Enum):
    """Enum of secret statuses"""

    CURRENT = "AWSCURRENT"
    PENDING = "AWSPENDING"
    PREVIOUS = "AWSPREVIOUS"
