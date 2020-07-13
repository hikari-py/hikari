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

__all__: typing.Final[typing.List[str]] = ["UndefinedType", "UNDEFINED", "count"]

import enum
import typing


class _UndefinedType:
    __slots__: typing.Sequence[str] = ()

    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return "UNDEFINED"

    def __str__(self) -> str:
        return "UNDEFINED"


# Using an enum enables us to use typing.Literal. MyPy has a special case for
# assuming that the number of instances of a specific enum is limited by design,
# whereas using a constant value does not provide that. In short, this allows
# MyPy to determine it can statically cast a value to a different type when
# we do `is` and `is not` checks on values, which removes the need for casts.
@typing.final
class _UndefinedTypeWrapper(_UndefinedType, enum.Enum):
    """Wrapper type around the undefined value.

    If you see this in a signature somewhere, it means you can pass a
    value of `UNDEFINED` and it will be valid.

    If you see this as the type of an attribute somewhere, it means that
    the attribute may be `UNDEFINED` in some edge cases.

    This exists to allow static type checkers to dereference this value
    using `typing.Literal`, which aids in static type analysis by treating
    this value as a true singleton. This can only be achieved by using
    an `enum.Enum` of a single value to enforce this.

    For all other purposes, you can treat this as the type of the
    `UNDEFINED` sentinel in this module. You should generally not need to
    use this, however.
    """

    # Don't document this.
    __pdoc__: typing.Final[typing.ClassVar[typing.Mapping[str, bool]]] = {
        "__init__": False,
        "UNDEFINED_VALUE": False,
    }

    UNDEFINED_VALUE = _UndefinedType()


# Prevent making any more instances as much as possible.
setattr(_UndefinedType, "__new__", NotImplemented)
del _UndefinedType


# noinspection PyTypeChecker
UNDEFINED: typing.Final[UndefinedType] = _UndefinedTypeWrapper.UNDEFINED_VALUE
"""Undefined sentinel value.

This will behave as a false value in conditions.
"""


if typing.TYPE_CHECKING:
    UndefinedType = typing.Literal[_UndefinedTypeWrapper.UNDEFINED_VALUE]
else:
    UndefinedType = type(UNDEFINED)


def count(*items: typing.Any) -> int:
    """Count the number of items that are provided that are `UNDEFINED`."""
    return sum(1 for item in items if item is UNDEFINED)
