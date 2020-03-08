#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright © Nekokatt 2019-2020
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
"""
Provides an automated repr generator.
"""
import reprlib
import typing


def repr_of(*args: str) -> typing.Callable[[typing.Any], str]:
    """
    Generates a `__repr__` method that outputs `{{type qualified name}}(arg1, arg2, ..., argN)` where
    each arg is the value of the attribute name passed to this function passed through the `repr` builtin function.

    .. code-block:: python

        @dataclasses.dataclass(repr=False)
        class User:
            id: int
            name: str
            nick: typing.Optional[str]
            role_ids: typing.Sequence[int]

            __repr__ = repr_of("id", "name", "nick")

            # ^-- this is analogous to specifying the following `__repr__` --v

            def __repr__(self):
                return f"User(id={self.id!r}, name={self.name!r}, nick={self.nick!r})"

    Args:
        *args:
            Zero or more attributes to use in the repr.

    Returns:
        A `__repr__` implementation that can be stored in a class variable called `__repr__` to use that implementation.
    """

    @reprlib.recursive_repr()
    def __repr__(self) -> str:
        elements = ", ".join(_repr_arg(self, arg) for arg in args)
        return f"{type(self).__name__}({elements})"

    return __repr__


def _repr_arg(self, attr):
    value = _getter(self, attr)
    return f"{attr}={value!r}"


def _getter(self, attr):
    queue = tuple(item for item in attr.split("."))

    for item in queue:
        self = getattr(self, item)
    return self
