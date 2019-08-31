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

from hikari.core.utils import delegate
from tests.hikari.core import _helpers


def test_DelegatedProperty_on_instance():
    class Inner:
        def __init__(self):
            self.a = 1234321

    class Outer:
        a = delegate.DelegatedProperty("inner", "a")

        def __init__(self, inner_):
            self.inner = inner_

    inner = Inner()
    outer = Outer(inner)
    assert outer.a == 1234321


def test_DelegatedProperty_on_owner():
    class Outer:
        a = delegate.DelegatedProperty("inner", "a")

    assert isinstance(Outer.a, delegate.DelegatedProperty)


@_helpers.assert_raises(TypeError)
def test_delegate_safe_dataclass_on_delegated_class_fails_test():
    class Delegated:
        pass

    setattr(Delegated, delegate._DELEGATE_MEMBERS_FIELD, [])
    delegate.delegate_safe_dataclass()(Delegated)


def test_delegate_safe_dataclass_with_no_fields():
    @delegate.delegate_safe_dataclass()
    class Test:
        __delegated_members__ = frozenset()
        __slots__ = ()

    Test()


def test_delegate_safe_dataclass_with_fields_and_no_delegated_members():
    @delegate.delegate_safe_dataclass()
    class Test:
        __delegated_members__ = frozenset()
        __slots__ = ("a", "b", "c")
        a: int
        b: int
        c: int

    Test(a=1, b=2, c=3)


def test_delegate_safe_dataclass_with_fields_does_not_initialize_delegated_members():
    @delegate.delegate_safe_dataclass()
    class Test:
        __delegated_members__ = frozenset({"d", "e", "f"})
        __slots__ = ("a", "b", "c", "d", "e", "f")
        a: int
        b: int
        c: int

    Test(a=1, b=2, c=3)


@_helpers.assert_raises(TypeError)
def test_delegate_safe_dataclass_with_fields_does_validate_non_delegated_dataclass_parameters():
    @delegate.delegate_safe_dataclass()
    class Test:
        __delegated_members__ = frozenset({"d", "e", "f"})
        __slots__ = ("a", "b", "c", "d", "e", "f")
        a: int
        b: int
        c: int

    Test(a=1, b=2)  # missing c parameter


def test_field_delegation():
    class Base:
        __slots__ = ("a", "b", "c")

        def __init__(self, a, b, c):
            self.a, self.b, self.c = a, b, c

    @delegate.delegate_members(Base, "_base")
    class Delegate(Base):
        __slots__ = ("_base", "d", "e", "f")
        _base: Base
        d: int
        e: int
        f: int

        def __init__(self, _base, d, e, f):
            self._base = _base
            self.d = d
            self.e = e
            self.f = f

    ba = Base(1, 2, 3)
    de = Delegate(ba, 4, 5, 6)
    assert de.a == 1
    assert de.b == 2
    assert de.c == 3
    assert de.d == 4 and "d" not in dir(ba)
    assert de.e == 5 and "e" not in dir(ba)
    assert de.f == 6 and "f" not in dir(ba)


def test_field_delegation_on_dataclass():
    @dataclasses.dataclass()
    class Base:
        a: int
        b: int
        c: int

    @delegate.delegate_members(Base, "_base")
    @delegate.delegate_safe_dataclass()
    class Delegate(Base):
        _base: Base
        d: int
        e: int
        f: int

    ba = Base(1, 2, 3)
    de = Delegate(ba, 4, 5, 6)

    assert de.a == 1
    assert de.b == 2
    assert de.c == 3
    assert de.d == 4
    assert de.e == 5
    assert de.f == 6
