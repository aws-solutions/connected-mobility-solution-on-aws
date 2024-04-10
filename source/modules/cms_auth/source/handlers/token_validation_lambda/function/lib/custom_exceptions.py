# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0


class TokenDecodeError(Exception):
    def __init__(self, message: str = "Token could not be decoded.", code: int = 401):
        self.message = message
        self.code = code


class TokenClaimsError(Exception):
    def __init__(self, message: str = "Token signature is invalid.", code: int = 401):
        self.message = message
        self.code = code


class ExpirationError(Exception):
    def __init__(self, message: str = "Token expiration is invalid.", code: int = 401):
        self.message = message
        self.code = code


class IdPAudError(Exception):
    def __init__(
        self,
        message: str = "Token aud is invalid.",
        code: int = 401,
    ):
        self.message = message
        self.code = code


class ScopeError(Exception):
    def __init__(self, message: str = "Token scope is invalid.", code: int = 401):
        self.message = message
        self.code = code


class WellKnownJWKError(Exception):
    def __init__(self, message: str = "Could not retrieve JWKs.", code: int = 500):
        self.message = message
        self.code = code


class SigningKidError(Exception):
    def __init__(
        self,
        message: str = "Token kid which signed this token is invalid.",
        code: int = 401,
    ):
        self.message = message
        self.code = code
