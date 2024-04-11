# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0


class GrafanaApiError(Exception):
    pass


class SecretRotationNotEnabledError(Exception):
    pass


class SecretRotationNotStagedError(Exception):
    pass


class InvalidSecretRotationStepError(Exception):
    pass
