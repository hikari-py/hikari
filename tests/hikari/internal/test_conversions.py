#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019-2020
#
# This file is part of Hikari.
#
# Hikari is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Hikari is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Hikari. If not, see <https://www.gnu.org/licenses/>.
import datetime
import typing

import pytest

from hikari.internal import conversions
from hikari.internal import unset


def test_put_if_specified_when_specified():
    d = {}
    conversions.put_if_specified(d, "foo", 69)
    conversions.put_if_specified(d, "bar", "hi")
    conversions.put_if_specified(d, "bar", None)
    assert d == {"foo": 69, "bar": None}


def test_put_if_specified_when_unspecified():
    d = {}
    conversions.put_if_specified(d, "bar", unset.UNSET)
    assert d == {}


def test_put_if_specified_when_type_after_passed():
    d = {}
    conversions.put_if_specified(d, "foo", 69, str)
    conversions.put_if_specified(d, "bar", "69", int)
    assert d == {"foo": "69", "bar": 69}


def test_parse_iso_8601_date_with_negative_timezone():
    string = "2019-10-10T05:22:33.023456-02:30"
    date = conversions.iso8601_datetime_string_to_datetime(string)
    assert date.year == 2019
    assert date.month == 10
    assert date.day == 10
    assert date.hour == 5
    assert date.minute == 22
    assert date.second == 33
    assert date.microsecond == 23456
    offset = date.tzinfo.utcoffset(None)
    assert offset == datetime.timedelta(hours=-2, minutes=-30)


def test_parse_iso_8601_date_with_positive_timezone():
    string = "2019-10-10T05:22:33.023456+02:30"
    date = conversions.iso8601_datetime_string_to_datetime(string)
    assert date.year == 2019
    assert date.month == 10
    assert date.day == 10
    assert date.hour == 5
    assert date.minute == 22
    assert date.second == 33
    assert date.microsecond == 23456
    offset = date.tzinfo.utcoffset(None)
    assert offset == datetime.timedelta(hours=2, minutes=30)


def test_parse_iso_8601_date_with_zulu():
    string = "2019-10-10T05:22:33.023456Z"
    date = conversions.iso8601_datetime_string_to_datetime(string)
    assert date.year == 2019
    assert date.month == 10
    assert date.day == 10
    assert date.hour == 5
    assert date.minute == 22
    assert date.second == 33
    assert date.microsecond == 23456
    offset = date.tzinfo.utcoffset(None)
    assert offset == datetime.timedelta(seconds=0)


def test_parse_iso_8601_date_with_milliseconds_instead_of_microseconds():
    string = "2019-10-10T05:22:33.023Z"
    date = conversions.iso8601_datetime_string_to_datetime(string)
    assert date.year == 2019
    assert date.month == 10
    assert date.day == 10
    assert date.hour == 5
    assert date.minute == 22
    assert date.second == 33
    assert date.microsecond == 23000


def test_parse_iso_8601_date_with_no_fraction():
    string = "2019-10-10T05:22:33Z"
    date = conversions.iso8601_datetime_string_to_datetime(string)
    assert date.year == 2019
    assert date.month == 10
    assert date.day == 10
    assert date.hour == 5
    assert date.minute == 22
    assert date.second == 33
    assert date.microsecond == 0


def test_parse_http_date():
    rfc_timestamp = "Mon, 03 Jun 2019 17:54:26 GMT"
    expected_timestamp = datetime.datetime(2019, 6, 3, 17, 54, 26, tzinfo=datetime.timezone.utc)
    assert conversions.rfc7231_datetime_string_to_datetime(rfc_timestamp) == expected_timestamp


def test_parse_discord_epoch_to_datetime():
    discord_timestamp = 37921278956
    expected_timestamp = datetime.datetime(2016, 3, 14, 21, 41, 18, 956000, tzinfo=datetime.timezone.utc)
    assert conversions.discord_epoch_to_datetime(discord_timestamp) == expected_timestamp


def test_parse_unix_epoch_to_datetime():
    unix_timestamp = 1457991678956
    expected_timestamp = datetime.datetime(2016, 3, 14, 21, 41, 18, 956000, tzinfo=datetime.timezone.utc)
    assert conversions.unix_epoch_to_datetime(unix_timestamp) == expected_timestamp


def test_unix_epoch_to_datetime_with_out_of_range_positive_timestamp():
    assert conversions.unix_epoch_to_datetime(996877846784536) == datetime.datetime.max


def test_unix_epoch_to_datetime_with_out_of_range_negative_timestamp():
    assert conversions.unix_epoch_to_datetime(-996877846784536) == datetime.datetime.min


@pytest.mark.parametrize(
    ["count", "name", "kwargs", "expect"],
    [
        (0, "foo", {}, "0 foos"),
        (1, "foo", {}, "1 foo"),
        (2, "foo", {}, "2 foos"),
        (0, "foo", dict(suffix="es"), "0 fooes"),
        (1, "foo", dict(suffix="es"), "1 foo"),
        (2, "foo", dict(suffix="es"), "2 fooes"),
    ],
)
def test_pluralize(count, name, kwargs, expect):
    assert conversions.pluralize(count, name, **kwargs) == expect


class TestResolveSignature:
    def test_handles_normal_references(self):
        def foo(bar: str, bat: int) -> str:
            ...

        signature = conversions.resolve_signature(foo)
        assert signature.parameters["bar"].annotation is str
        assert signature.parameters["bat"].annotation is int
        assert signature.return_annotation is str

    def test_handles_normal_no_annotations(self):
        def foo(bar, bat):
            ...

        signature = conversions.resolve_signature(foo)
        assert signature.parameters["bar"].annotation is conversions.EMPTY
        assert signature.parameters["bat"].annotation is conversions.EMPTY
        assert signature.return_annotation is conversions.EMPTY

    def test_handles_forward_annotated_parameters(self):
        def foo(bar: "str", bat: "int") -> str:
            ...

        signature = conversions.resolve_signature(foo)
        assert signature.parameters["bar"].annotation is str
        assert signature.parameters["bat"].annotation is int
        assert signature.return_annotation is str

    def test_handles_forward_annotated_return(self):
        def foo(bar: str, bat: int) -> "str":
            ...

        signature = conversions.resolve_signature(foo)
        assert signature.parameters["bar"].annotation is str
        assert signature.parameters["bat"].annotation is int
        assert signature.return_annotation is str

    def test_handles_forward_annotations(self):
        def foo(bar: "str", bat: "int") -> "str":
            ...

        signature = conversions.resolve_signature(foo)
        assert signature.parameters["bar"].annotation is str
        assert signature.parameters["bat"].annotation is int
        assert signature.return_annotation is str

    def test_handles_mixed_annotations(self):
        def foo(bar: str, bat: "int"):
            ...

        signature = conversions.resolve_signature(foo)
        assert signature.parameters["bar"].annotation is str
        assert signature.parameters["bat"].annotation is int
        assert signature.return_annotation is conversions.EMPTY

    def test_handles_only_return_annotated(self):
        def foo(bar, bat) -> str:
            ...

        signature = conversions.resolve_signature(foo)
        assert signature.parameters["bar"].annotation is conversions.EMPTY
        assert signature.parameters["bat"].annotation is conversions.EMPTY
        assert signature.return_annotation is str

    def test_handles_nested_annotations(self):
        def foo(bar: typing.Optional[typing.Iterator[int]]):
            ...

        signature = conversions.resolve_signature(foo)
        assert signature.parameters["bar"].annotation == typing.Optional[typing.Iterator[int]]
