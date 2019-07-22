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

import pytest

from hikari.utils import delegate


def test_field_delegation():
    @dataclasses.dataclass()
    class Base:
        __slots__ = ("a", "b", "c")
        a: int
        b: int
        c: int

    @delegate.delegate_safe_dataclass()
    @delegate.delegate_members(Base, "_base")
    class Delegate(Base):
        __slots__ = ("_base",)
        _base: Base

    b = Base(1, 2, 3)
    d = Delegate(b)
    assert d.a == 1
    assert d.b == 2
    assert d.c == 3


def test_function_delegation():
    pass
