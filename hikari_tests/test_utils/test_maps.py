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
import datetime

from hikari.utils import maps, unspecified


def test_put_if_specified_when_specified():
    d = {}
    maps.put_if_specified(d, "foo", 69)
    maps.put_if_specified(d, "bar", "hi")
    maps.put_if_specified(d, "bar", None)
    assert d == {"foo": 69, "bar": None}


def test_put_if_specified_when_unspecified():
    d = {}
    maps.put_if_specified(d, "bar", unspecified.UNSPECIFIED)
    assert d == {}


def test_get_from_map_as_when_value_is_right_type():
    d = {"foo": 9, "bar": 18}
    assert maps.get_from_map_as(d, "foo", int) == 9


def test_get_from_map_as_when_value_is_not_right_type():
    d = {"foo": 9, "bar": 18}
    assert maps.get_from_map_as(d, "bar", str) == "18"


def test_get_from_map_as_value_when_not_present_returns_None():
    d = {"foo": 9, "bar": 18}
    assert maps.get_from_map_as(d, "baz", int) is None


def test_get_from_map_as_value_when_not_present_with_custom_default_returns_that_default():
    d = {"foo": 9, "bar": 18}
    sentinel = object()
    assert maps.get_from_map_as(d, "baz", int, sentinel) is sentinel


def test_get_from_map_as_value_when_cast_error_not_suppressed_raises_exception():
    d = {"foo": 9, "bar": 18, "baz": {9, 18, 27}}
    try:
        maps.get_from_map_as(d, "baz", datetime.timedelta)
        assert False, "Error did not propagate"
    except Exception:
        assert True, "Success. Error is raised"


def test_get_from_map_as_value_when_cast_error_suppressed_returns_default():
    d = {"foo": 9, "bar": 18, "baz": {9, 18, 27}}
    assert maps.get_from_map_as(d, "baz", datetime.timedelta, default_on_error=True) is None
