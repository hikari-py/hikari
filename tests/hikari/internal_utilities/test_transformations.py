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
