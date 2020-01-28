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
from __future__ import annotations

import dataclasses
import typing

from hikari.internal_utilities import type_hints
from hikari.internal_utilities import reprs


def test_repr_with_no_args():
    @dataclasses.dataclass()
    class User:
        id: int
        name: str
        nick: type_hints.Nullable[str]
        roles: typing.Sequence[int]

        __repr__ = reprs.repr_of()

    u = User(123, "foo", None, [1, 2, 3])
    assert repr(u) == "User()"


def test_repr_with_args():
    @dataclasses.dataclass()
    class User:
        id: int
        name: str
        nick: type_hints.Nullable[str]
        roles: typing.Sequence[int]

        __repr__ = reprs.repr_of("id", "name")

    u = User(123, "foo", None, [1, 2, 3])
    assert repr(u) == "User(id=123, name='foo')"


def test_repr_with_nested_args():
    @dataclasses.dataclass()
    class Role:
        id: int
        name: str
        color: int

    @dataclasses.dataclass()
    class User:
        id: int
        name: str
        nick: type_hints.Nullable[str]
        role: Role

        __repr__ = reprs.repr_of("id", "role.name")

    u = User(123, "foo", None, Role(1234, "bar", 0xFFFFFF))
    assert repr(u) == "User(id=123, role.name='bar')"


def test_repr_with_recursive_repr_calls():
    class Person:
        def __init__(self, name):
            self.name = name
            self.children = []
            self.spouse = None
            self.mother = None
            self.father = None

        __repr__ = reprs.repr_of("name", "children", "spouse", "mother", "father")

    mother = Person("mother")
    father = Person("father")
    mother.spouse = father
    father.spouse = mother

    me = Person("nekokatt")
    mother.children.append(me)
    father.children.append(me)
    me.mother = mother
    me.father = father

    expect = (
        "Person(name='nekokatt', children=[], spouse=None, mother=Person(name"
        "='mother', children=[...], spouse=Person(name='father', children=[...],"
        " spouse=..., mother=None, father=None), mother=None, father=None), "
        "father=Person(name='father', children=[...], spouse=Person(name="
        "'mother', children=[...], spouse=..., mother=None, father=None), "
        "mother=None, father=None))"
    )

    assert repr(me) == expect
