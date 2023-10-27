# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Standard Library
from enum import Enum


class CustomResourceType:
    class RequestType(Enum):
        CREATE = "Create"
        UPDATE = "Update"
        DELETE = "Delete"

    class ResourceType(Enum):
        LOAD_OR_CREATE_IOT_CREDENTIALS = "LoadOrCreateIoTCredentials"
        UPDATE_EVENT_CONFIGURATIONS = "UpdateEventConfigurations"
        DELETE_PROVISIONING_CERTIFICATE = "DeleteProvisioningCertificate"

    class StatusType(Enum):
        SUCCESS = "SUCCESS"
        FAILED = "FAILED"
