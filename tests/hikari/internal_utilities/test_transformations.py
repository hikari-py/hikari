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
import dataclasses
import typing
import cymock as mock

import pytest

from hikari.internal_utilities import transformations
from hikari.internal_utilities import unspecified


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
    assert transformations.nullable_cast(value, cast) == expect


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
    assert transformations.try_cast(value, cast, default) == expect


def test_put_if_specified_when_specified():
    d = {}
    transformations.put_if_specified(d, "foo", 69)
    transformations.put_if_specified(d, "bar", "hi")
    transformations.put_if_specified(d, "bar", None)
    assert d == {"foo": 69, "bar": None}


def test_put_if_specified_when_unspecified():
    d = {}
    transformations.put_if_specified(d, "bar", unspecified.UNSPECIFIED)
    assert d == {}


def test_put_if_specified_when_type_after_passed():
    d = {}
    transformations.put_if_specified(d, "foo", 69, str)
    transformations.put_if_specified(d, "bar", "69", int)
    assert d == {"foo": "69", "bar": 69}


def test_get_id_for_model():
    obj = mock.MagicMock()
    obj.id = 123
    assert transformations.get_id(obj.id) == "123"


@pytest.mark.parametrize("value", ["123", 123])
def test_get_id_for_sparse_value(value):
    assert transformations.get_id(value) == "123"


@pytest.mark.parametrize(
    ["data", "cast_called", "nullable"],
    [("123123", True, False), (unspecified.UNSPECIFIED, False, False), (None, False, True), (None, True, False),],
)
def test_cast_if_specified(data, cast_called, nullable):
    mock_result = mock.MagicMock()
    mock_cast = mock.MagicMock(str, return_value=mock_result)
    result = transformations.cast_if_specified(data, mock_cast, nullable=nullable)
    if cast_called:
        assert result is mock_result
        mock_cast.assert_called_once_with(data)
    else:
        assert result is data
        mock_cast.assert_not_called()


@pytest.mark.parametrize(
    ["data", "cast_called", "nullable"],
    [(["123123",], True, False), (unspecified.UNSPECIFIED, False, False), (None, False, True),],
)
def test_cast_if_specified_with_iterable(data, cast_called, nullable):
    mock_result = mock.MagicMock()
    mock_cast = mock.MagicMock(str, return_value=mock_result)
    result = transformations.cast_if_specified(data, mock_cast, nullable=nullable, iterable=True)
    if cast_called:
        assert result == [mock_result]
        for entry in data:
            mock_cast.assert_called_once_with(entry)
    else:
        assert result is data
        mock_cast.assert_not_called()


def test_put_if_not_None_when_not_None():
    d = {}
    transformations.put_if_not_none(d, "foo", 69)
    transformations.put_if_not_none(d, "bar", "hi")
    assert d == {"foo": 69, "bar": "hi"}


def test_put_if_not_None_when_None():
    d = {}
    transformations.put_if_not_none(d, "bar", None)
    assert d == {}


def test_put_if_not_none_when_type_after_passed():
    d = {}
    transformations.put_if_not_none(d, "foo", 69, str)
    transformations.put_if_not_none(d, "bar", "69", int)
    assert d == {"foo": "69", "bar": 69}


@pytest.mark.parametrize(
    ["fmt", "kwargs", "expect"],
    [
        ("{foo} {bar} {baz}", dict(foo=9, baz=27), "9 {bar} 27"),
        ("{foo} {foo} {FOO}", dict(foo=9, baz=27), "9 9 {FOO}"),
        ("{{foo}} {foo} {FOO}", dict(foo=9, baz=27), "{foo} 9 {FOO}"),
    ],
)
def test_format_present_placeholders(fmt, kwargs, expect):
    assert transformations.format_present_placeholders(fmt, **kwargs) == expect


class IdObject:
    def __init__(self, id):
        self.id = id

    def __int__(self):
        return self.id


@pytest.mark.parametrize(
    ["model", "parent", "expected_result"],
    [
        (12354123, IdObject(32341223), "32341223"),
        (mock.MagicMock(attr=IdObject(222222)), 123123123, "123123123"),
        (mock.MagicMock(attr=IdObject(32123123)), unspecified.UNSPECIFIED, "32123123",),
    ],
)
def test_get_parent_id_from_model(model, parent, expected_result):
    assert transformations.get_parent_id_from_model(model, parent, "attr") == expected_result


def test_get_parent_id_from_model_raises_exception():
    try:
        transformations.get_parent_id_from_model(1234, unspecified.UNSPECIFIED, "attr")
        assert False, "Expected TypeError."
    except TypeError:
        ...


def test_id_map():
    @dataclasses.dataclass()
    class IDable:
        id: int
        name: str

    a = IDable(12, "Nekokatt")
    b = IDable(22, "Something else")
    c = IDable(-24, "Negative")
    elements = (a, b, c)
    result = transformations.id_map(elements)
    assert isinstance(result, typing.MutableMapping)
    assert result[12] is a
    assert result[22] is b
    assert result[-24] is c


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
    assert transformations.image_bytes_to_image_data(img_bytes) == expect


def test_image_bytes_to_image_data_when_None_returns_None():
    assert transformations.image_bytes_to_image_data(None) is None


def test_image_bytes_to_image_data_when_unsuported_image_type_raises_value_error():
    try:
        transformations.image_bytes_to_image_data(b"")
        assert False
    except ValueError:
        assert True


@pytest.mark.parametrize(
    ["guild_id", "shard_count", "expected_shard_id"],
    [(574921006817476608, 1, 0), (574921006817476608, 2, 1), (574921006817476608, 3, 2), (574921006817476608, 4, 1)],
)
def test_guild_id_to_shard_id(guild_id, shard_count, expected_shard_id):
    assert transformations.guild_id_to_shard_id(guild_id, shard_count) == expected_shard_id
