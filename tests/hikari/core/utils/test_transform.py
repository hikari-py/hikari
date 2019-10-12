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


def test_format_present_placeholders():
    assert transform.format_present_placeholders("{foo} {bar} {baz}", foo=9, baz=27) == "9 {bar} 27"
