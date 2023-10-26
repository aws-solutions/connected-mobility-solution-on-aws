# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from enum import Enum


# These mostly match certificate status provided by IoT Core, however, we add a "DELETED" option here to track deleted certificates
class CertificateStatus(Enum):
    INACTIVE = "INACTIVE"
    ACTIVE = "ACTIVE"
    PENDING_ACTIVATION = "PENDING_ACTIVATION"
    DELETED = "DELETED"
