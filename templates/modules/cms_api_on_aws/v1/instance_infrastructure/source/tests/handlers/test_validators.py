# -*- coding: utf-8 -*-
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0

# Third Party Libraries
import pytest

# Connected Mobility Solution on AWS
from ...handlers.athena_data_source.lib.athena_exceptions import AthenaQueryError
from ...handlers.athena_data_source.lib.validators import (
    validate_query_selection_string,
    validate_query_table_name,
    validate_query_vin_input,
)


@pytest.mark.parametrize(
    "selection_string, throws_error",
    [
        ('"test" as "test"', False),
        ('"test1"."test2"."test3" as "test1.test2.test3"', False),
        (
            '"test1"."test2"."test3" as "test1.test2.test3", "test4"."test5"."test6" as "test4.test5.test6"',
            False,
        ),
        ('"test1"."fail;"."test3" as "test1.test2.test3"', True),
        ("no.quotes.test as no.quotes.test", True),
        (
            '"test1"."test2"."test3" as "test1.test2.test3"\nsome-dangerous-newline-string',
            True,
        ),
    ],
)
def test_validate_query_selection_string(
    selection_string: str, throws_error: bool
) -> None:
    if throws_error:
        with pytest.raises(AthenaQueryError):
            validate_query_selection_string(selection_string)
    else:
        validate_query_selection_string(selection_string)


@pytest.mark.parametrize(
    "table_name, throws_error",
    [
        ("test-table-name-with-dashes", False),
        ("test_table_name_with_underscores", False),
        ("test-table-name-with-numbers-123", False),
        ("test table name with spaces", True),
        ("test.table.name.with.periods", True),
        ("test;table;name;with;semicolons", True),
        ("test-table-name-with-dashes\nsome-dangerous-newline-string", True),
    ],
)
def test_validate_query_table_name(table_name: str, throws_error: bool) -> None:
    if throws_error:
        with pytest.raises(AthenaQueryError):
            validate_query_table_name(table_name)
    else:
        validate_query_table_name(table_name)


@pytest.mark.parametrize(
    "vin_input, throws_error",
    [
        ("ABCDEFGHIJ12345678", False),
        ("ABCDEFGHIJ1234567_", True),
        ("ABCDEFGHIJ1234567;", True),
        ("ABCDEFGHIJ1234567.", True),
        ("ABCDEFGHIJ1234567 ", True),
    ],
)
def test_validate_query_vin_input(vin_input: str, throws_error: bool) -> None:
    if throws_error:
        with pytest.raises(AthenaQueryError):
            validate_query_vin_input(vin_input)
    else:
        validate_query_vin_input(vin_input)
