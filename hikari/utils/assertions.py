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
"""
Assertions of things. These are functions that validate a value, expected to return the value on success but error
on any failure.
"""
__all__ = ("assert_not_none", "assert_is_slotted", "assert_is_mixin")

import typing

T = typing.TypeVar("T")


def assert_not_none(value: T, description: str = "value") -> T:
    """Raises a ValueError with the optional description if the given value is None."""
    if value is None:
        raise ValueError(f"{description} must not be None")
    return value


def assert_is_slotted(cls: typing.Type[T]) -> typing.Type[T]:
    """Raises a TypeError if the class is not slotted."""
    if not hasattr(cls, "__slots__"):
        raise TypeError(f"Class {cls.__qualname__} is required to be slotted.")
    return cls


def assert_is_mixin(cls: typing.Type[T]) -> typing.Type[T]:
    """
    Checks whether the item is mixin-compatible or not.

    An object is mixin compatible only if:

        1. It is a class.
        2. It can only subclass :class:`object` or a class that is also mixin compatible.
        3. It must be slotted.
        4. The slots must be completely empty.
        5. The name must end with the word "Mixin".

    Raises a TypeError if the class is not mixin-compatible, or a NameError if it is badly named for a mixin.

    """
    if not isinstance(cls, type):
        raise TypeError(f"Object {cls} is marked as a mixin but does not derive from metaclass {type}.")
    if cls.mro() != [cls, object]:
        for parent_cls in cls.mro()[1:-1]:
            try:
                assert_is_mixin(parent_cls)
            except TypeError as ex:
                raise TypeError(
                    f"Object {cls.__qualname__} is marked as a mixin but derives from {parent_cls.__qualname__} which"
                    "is not a mixin."
                ) from ex

    assert_is_slotted(cls)

    if len(cls.__slots__) > 0:
        raise TypeError(f"Class {cls.__qualname__} is a mixin so must NOT declare any fields. Slots should be empty.")
    if not cls.__qualname__.endswith("Mixin"):
        raise NameError(f'Class {cls.__qualname__} is defined as a mixin but does not have a name ending in "Mixin".')

    return cls
