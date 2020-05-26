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
"""Sentinel for an unset value or attribute."""

from __future__ import annotations

__all__ = ["Unset", "UNSET", "is_unset"]

import typing

from hikari.internal import meta


class Unset(meta.Singleton):
    """A singleton value that represents an unset field.

    This will always have a falsified value.
    """

    __slots__ = ()

    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return type(self).__name__.upper()

    def __iter__(self) -> typing.Iterator[None]:
        yield from ()

    __str__ = __repr__

    def __init_subclass__(cls, **kwargs: typing.Any) -> typing.NoReturn:
        raise TypeError("Cannot subclass Unset type")


T = typing.TypeVar("T", contravariant=True)

UNSET: typing.Final[Unset] = Unset()
"""A global instance of `Unset`."""


@typing.overload
def is_unset(obj: UNSET) -> typing.Literal[True]:
    """Return `True` always."""


@typing.overload
def is_unset(obj: typing.Any) -> typing.Literal[False]:
    """Return `False` always."""


def is_unset(obj):
    """Return `True` if the object is an `Unset` value."""
    return isinstance(obj, Unset)


def count_unset_objects(obj1: typing.Any, obj2: typing.Any, *objs: typing.Any) -> int:
    """Count the number of objects that are unset in the provided parameters."""
    return sum(is_unset(o) for o in (obj1, obj2, *objs))
