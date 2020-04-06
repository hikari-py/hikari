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
import concurrent.futures
import datetime
import inspect
import io

import cymock as mock
import pytest
import typing

from hikari.internal import conversions
from tests.hikari import _helpers


@pytest.mark.parametrize(
    ["value", "cast", "expect"],
    [
        ("22", int, 22),
        (None, int, None),
        ("22", lambda a: float(a) / 10 + 7, 9.2),
        (None, lambda a: float(a) / 10 + 7, None),
    ],
)
def test_nullable_cast(value, cast, expect):
    assert conversions.nullable_cast(value, cast) == expect


@pytest.mark.parametrize(
    ["value", "cast", "default", "expect"],
    [
        ("hello", int, "dead", "dead"),
        ("22", int, "dead", 22),
        ("22", lambda n: n + 4, ..., ...),
        (22, lambda n: n + 4, ..., 26),
    ],
)
def test_try_cast(value, cast, default, expect):
    assert conversions.try_cast(value, cast, default) == expect


def test_put_if_specified_when_specified():
    d = {}
    conversions.put_if_specified(d, "foo", 69)
    conversions.put_if_specified(d, "bar", "hi")
    conversions.put_if_specified(d, "bar", None)
    assert d == {"foo": 69, "bar": None}


def test_put_if_specified_when_unspecified():
    d = {}
    conversions.put_if_specified(d, "bar", ...)
    assert d == {}


def test_put_if_specified_when_type_after_passed():
    d = {}
    conversions.put_if_specified(d, "foo", 69, str)
    conversions.put_if_specified(d, "bar", "69", int)
    assert d == {"foo": "69", "bar": 69}


@pytest.mark.parametrize(
    ["img_bytes", "expect"],
    [
        (b"\211PNG\r\n\032\n", "data:image/png;base64,iVBORw0KGgo="),
        (b"      Exif", "data:image/jpeg;base64,ICAgICAgRXhpZg=="),
        (b"      JFIF", "data:image/jpeg;base64,ICAgICAgSkZJRg=="),
        (b"GIF87a", "data:image/gif;base64,R0lGODdh"),
        (b"GIF89a", "data:image/gif;base64,R0lGODlh"),
        (b"RIFF    WEBP", "data:image/webp;base64,UklGRiAgICBXRUJQ"),
    ],
)
def test_image_bytes_to_image_data_img_types(img_bytes, expect):
    assert conversions.image_bytes_to_image_data(img_bytes) == expect


def test_image_bytes_to_image_data_when_None_returns_None():
    assert conversions.image_bytes_to_image_data(None) is None


def test_image_bytes_to_image_data_when_unsupported_image_type_raises_value_error():
    try:
        conversions.image_bytes_to_image_data(b"")
        assert False
    except ValueError:
        assert True


def test_parse_iso_8601_date_with_negative_timezone():
    string = "2019-10-10T05:22:33.023456-02:30"
    date = conversions.parse_iso_8601_ts(string)
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
    date = conversions.parse_iso_8601_ts(string)
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
    date = conversions.parse_iso_8601_ts(string)
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
    date = conversions.parse_iso_8601_ts(string)
    assert date.year == 2019
    assert date.month == 10
    assert date.day == 10
    assert date.hour == 5
    assert date.minute == 22
    assert date.second == 33
    assert date.microsecond == 23000


def test_parse_iso_8601_date_with_no_fraction():
    string = "2019-10-10T05:22:33Z"
    date = conversions.parse_iso_8601_ts(string)
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
    assert conversions.parse_http_date(rfc_timestamp) == expected_timestamp


def test_parse_discord_epoch_to_datetime():
    discord_timestamp = 37921278956
    expected_timestamp = datetime.datetime(2016, 3, 14, 21, 41, 18, 956000, tzinfo=datetime.timezone.utc)
    assert conversions.discord_epoch_to_datetime(discord_timestamp) == expected_timestamp


def test_parse_unix_epoch_to_datetime():
    unix_timestamp = 1457991678956
    expected_timestamp = datetime.datetime(2016, 3, 14, 21, 41, 18, 956000, tzinfo=datetime.timezone.utc)
    assert conversions.unix_epoch_to_datetime(unix_timestamp) == expected_timestamp


@pytest.mark.parametrize(
    ["input_arg", "expected_result_type"],
    [
        ("hello", io.StringIO),
        (b"hello", io.BytesIO),
        (bytearray("hello", "utf-8"), io.BytesIO),
        (memoryview(b"hello"), io.BytesIO),
    ],
)
def test_make_resource_seekable(input_arg, expected_result_type):
    assert isinstance(conversions.make_resource_seekable(input_arg), expected_result_type)


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


class TestSnoopTypeHints:
    def test_snoop_simple_local_scope(self):
        x = object()

        frame = inspect.stack(1)[0][0]
        try:
            assert conversions.snoop_typehint_from_scope(frame, "x") is x
        finally:
            del frame

    def test_snoop_simple_global_scope(self):
        frame = inspect.stack(1)[0][0]
        try:
            assert conversions.snoop_typehint_from_scope(frame, "pytest") is pytest
        finally:
            del frame

    # noinspection PyUnusedLocal
    def test_snoop_nested_local_scope(self):
        expected = object()

        class Foo:
            class Bar:
                class Baz:
                    class Bork:
                        qux = expected

        frame = inspect.stack(1)[0][0]
        try:
            assert conversions.snoop_typehint_from_scope(frame, "Foo.Bar.Baz.Bork.qux") is expected
        finally:
            del frame

    def test_snoop_nested_global_scope(self):
        frame = inspect.stack(1)[0][0]
        try:
            assert (
                conversions.snoop_typehint_from_scope(frame, "concurrent.futures.as_completed")
                is concurrent.futures.as_completed
            )
        finally:
            del frame

    def test_snoop_on_resolved_typehint_does_nothing(self):
        frame = inspect.stack(1)[0][0]
        try:
            assert conversions.snoop_typehint_from_scope(frame, typing.Sequence) is typing.Sequence
        finally:
            del frame

    @_helpers.assert_raises(type_=NameError)
    def test_not_resolved_is_failure(self):
        attr = "this_is_not_an_attribute"
        assert attr not in locals(), "change this attribute name to something else so the test can run"
        assert attr not in globals(), "change this attribute name to something else so the test can run"

        frame = inspect.stack(1)[0][0]
        try:
            conversions.snoop_typehint_from_scope(frame, attr)
        finally:
            del frame


@pytest.mark.parametrize(
    "input",
    [
        b"hello",
        bytearray("hello", "utf-8"),
        memoryview(b"hello"),
        io.BytesIO(b"hello"),
        mock.MagicMock(io.BufferedRandom, read=mock.MagicMock(return_value=b"hello")),
        mock.MagicMock(io.BufferedReader, read=mock.MagicMock(return_value=b"hello")),
        mock.MagicMock(io.BufferedRWPair, read=mock.MagicMock(return_value=b"hello")),
    ],
)
def test_get_bytes_from_resource(input):
    assert conversions.get_bytes_from_resource(input) == b"hello"
    if isinstance(input, mock.MagicMock):
        input.read.assert_called_once()
