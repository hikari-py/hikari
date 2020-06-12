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
"""Singleton used throughout the library to denote values that are not present."""

from __future__ import annotations

__all__: typing.List[str] = ["UndefinedType", "UNDEFINED"]

# noinspection PyUnresolvedReferences
import typing


class _UndefinedType:
    __slots__ = ()

    def __bool__(self) -> bool:
        return False

    def __init_subclass__(cls, **kwargs) -> None:
        raise TypeError("Cannot subclass UndefinedType")

    def __repr__(self) -> str:
        return "<undefined value>"

    def __str__(self) -> str:
        return "UNDEFINED"


# Only expose correctly for static type checkers. Prevents anyone misusing it
# outside of simply checking `if value is UNDEFINED`.
UndefinedType = _UndefinedType if typing.TYPE_CHECKING else object()
"""Type hint describing the type of `UNDEFINED` used for type hints

This is a purely sentinel type hint at runtime, and will not support instance
checking.
"""

UNDEFINED: typing.Final[_UndefinedType] = _UndefinedType()
"""Undefined sentinel value.

This will behave as a false value in conditions.
"""

# Prevent making any more instances as much as possible.
_UndefinedType.__new__ = NotImplemented
_UndefinedType.__init__ = NotImplemented

# Remove the reference here.
del _UndefinedType


def count(*items: typing.Any) -> int:
    """Count the number of items that are provided that are UNDEFINED."""
    return sum(1 for item in items if item is UNDEFINED)
