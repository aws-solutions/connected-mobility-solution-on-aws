# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0


class RegexPattern:
    EMAIL = r"^[_A-Za-z0-9-\+]+(\.[_A-Za-z0-9-]+)*@[A-Za-z0-9-]+(\.[A-Za-z0-9]+)*(\.[A-Za-z]{2,})$"
    OPTIONAL_EMAIL = r"(^$)|^[_A-Za-z0-9-\+]+(\.[_A-Za-z0-9-]+)*@[A-Za-z0-9-]+(\.[A-Za-z0-9]+)*(\.[A-Za-z]{2,})$"
    DOMAIN_NAME = r"^([A-Za-z0-9][A-Za-z0-9-]*\.)+[A-Za-z]+$"
    CALLBACK_URLS = r"^(https:\/\/|http:\/\/localhost|(?!http:\/\/(?!localhost))[a-zA-Z0-9+-.]*:\/\/)[a-zA-Z0-9\\!$%&'()*+,\-./:;<=>?@\[\]^_`{|}~]{1,1024}(?!#)$"
    SCOPES = r"^(?:[^\s]+(?: [^\s]+)*)?$"
    SECRETSMANAGER_SECRET_ARN = r"(^$)|(arn:aws:secretsmanager:[a-z0-9-]+:\d{12}:secret:[a-zA-Z0-9/_+=.@-]+)"  # nosec
    APP_UNIQUE_ID = r"^(?!-)[a-z0-9-]+(?<!-)$"
    GENERIC_NAME = r"^[A-Za-z0-9][A-Za-z0-9-_ ]*[A-Za-z0-9]$"
    BEARER_TOKEN_AUTH_HEADER = r"^Bearer [\w-]+\.[\w-]+\.[\w-]+$"  # nosec
    S3_PATH_PREFIX = r"^[a-zA-Z0-9._-]+(?:/[a-zA-Z0-9._-]+)*$"
