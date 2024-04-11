# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0


class AuthorizationCodeExchangeError(Exception):
    def __init__(
        self,
        message: str = "Error while exchanging tokens using the found domain and client config.",
        code: int = 401,
    ):
        self.message = message
        self.code = code
