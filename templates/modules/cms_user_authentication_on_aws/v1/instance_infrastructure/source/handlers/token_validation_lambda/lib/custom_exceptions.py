# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0


class TokenExchangeError(Exception):
    pass


class TokenValidationError(Exception):
    pass


class TokenExpirationError(Exception):
    pass


class UserClaimsError(Exception):
    pass
