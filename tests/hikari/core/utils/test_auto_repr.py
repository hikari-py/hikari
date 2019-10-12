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

import typing

from hikari.core.utils import auto_repr


def test_repr_with_no_args():
    @dataclasses.dataclass()
    class User:
        id: int
        name: str
        nick: typing.Optional[str]
        roles: typing.Sequence[int]

        __repr__ = auto_repr.repr_of()

    u = User(123, "foo", None, [1, 2, 3])
    assert repr(u) == "User()"


def test_repr_with_args():
    @dataclasses.dataclass()
    class User:
        id: int
        name: str
        nick: typing.Optional[str]
        roles: typing.Sequence[int]

        __repr__ = auto_repr.repr_of("id", "name")

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
        nick: typing.Optional[str]
        role: Role

        __repr__ = auto_repr.repr_of("id", "role.name")

    u = User(123, "foo", None, Role(1234, "bar", 0xFFFFFF))
    assert repr(u) == "User(id=123, role.name='bar')"
