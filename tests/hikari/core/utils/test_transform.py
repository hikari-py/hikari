#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekoka.tt 2019
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
import datetime
import enum

from hikari.core.utils import transform
from hikari.core.utils import unspecified


def test_put_if_specified_when_specified():
    d = {}
    transform.put_if_specified(d, "foo", 69)
    transform.put_if_specified(d, "bar", "hi")
    transform.put_if_specified(d, "bar", None)
    assert d == {"foo": 69, "bar": None}


def test_put_if_specified_when_unspecified():
    d = {}
    transform.put_if_specified(d, "bar", unspecified.UNSPECIFIED)
    assert d == {}


def test_get_from_map_as_when_value_is_right_type():
    d = {"foo": 9, "bar": 18}
    assert transform.get_cast(d, "foo", int) == 9


def test_get_from_map_as_when_value_is_not_right_type():
    d = {"foo": 9, "bar": 18}
    assert transform.get_cast(d, "bar", str) == "18"


def test_get_cast_when_not_present_returns_None():
    d = {"foo": 9, "bar": 18}
    assert transform.get_cast(d, "baz", int) is None


def test_get_cast_when_not_present_with_custom_default_returns_that_default():
    d = {"foo": 9, "bar": 18}
    sentinel = object()
    assert transform.get_cast(d, "baz", int, sentinel) is sentinel


def test_get_cast_when_cast_error_not_suppressed_raises_exception():
    d = {"foo": 9, "bar": 18, "baz": {9, 18, 27}}
    try:
        transform.get_cast(d, "baz", datetime.timedelta)
        assert False, "Error did not propagate"
    except Exception:
        assert True, "Success. Error is raised"


def test_get_cast_when_cast_error_suppressed_returns_default():
    d = {"foo": 9, "bar": 18, "baz": {9, 18, 27}}
    assert transform.get_cast(d, "baz", datetime.timedelta, default_on_error=True) is None


def test_get_cast_or_raw_when_present():
    class Enum(enum.IntEnum):
        FOO = 1
        BAR = 2
        BAZ = 3

    items = {"qux": 2}

    value = transform.get_cast_or_raw(items, "qux", Enum)
    assert value == Enum.BAR


def test_get_cast_or_raw_when_present_via_transformation_method():
    class Enum(enum.IntEnum):
        FOO = 1
        BAR = 2
        BAZ = 3

        @staticmethod
        def transform(num):
            return Enum(num / 11)

    items = {"qux": 22}

    value = transform.get_cast_or_raw(items, "qux", Enum.transform)
    assert value == Enum.BAR


def test_get_cast_or_raw_when_present_via_name():
    class Enum(enum.IntEnum):
        FOO = 1
        BAR = 2
        BAZ = 3

    items = {"qux": "BAR"}

    value = transform.get_cast_or_raw(items, "qux", Enum.__getitem__)
    assert value == Enum.BAR


def test_get_cast_or_raw_when_value_not_recognised_outputs_input_value():
    class Enum(enum.IntEnum):
        FOO = 1
        BAR = 2
        BAZ = 3

    items = {"qux": 4}

    value = transform.get_cast_or_raw(items, "qux", Enum)
    assert value == 4


def test_get_cast_or_raw_when_value_not_present_outputs_None_value():
    class Enum(enum.IntEnum):
        FOO = 1
        BAR = 2
        BAZ = 3

    items = {}

    value = transform.get_cast_or_raw(items, "qux", Enum)
    assert value is None


def test_flatten_list():
    @dataclasses.dataclass()
    class Obj:
        id: int
        value: float

    o1 = Obj(99, 123.45)
    o2 = Obj(88, 696969696.271)
    o3 = Obj(32, 33.4)

    mapping = transform.flatten([o1, o2, o3], "id")
    assert mapping[99] is o1
    assert mapping[88] is o2
    assert mapping[32] is o3


def test_Volatile_update():
    @dataclasses.dataclass()
    class Base:
        foo: str
        bar: transform.volatile(str)

    base = Base("hello", "world")
    new = Base("blah", "blep")

    transform.update_volatile_fields(base, new)
    assert base.foo == "hello"
    assert base.bar == "blep"
