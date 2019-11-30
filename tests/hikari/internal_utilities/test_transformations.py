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

from hikari.internal_utilities import transformations
from hikari.internal_utilities import unspecified


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


def test_format_present_placeholders():
    assert transformations.format_present_placeholders("{foo} {bar} {baz}", foo=9, baz=27) == "9 {bar} 27"
