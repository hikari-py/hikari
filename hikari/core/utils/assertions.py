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
import inspect

import typing

T = typing.TypeVar("T")
U = typing.TypeVar("U")


def assert_not_none(value: T, description: str = "value") -> T:
    """Raises a ValueError with the optional description if the given value is None."""
    if value is None:
        raise ValueError(f"{description} must not be None")
    return value


def assert_is_natural(value: T, description: str = "value") -> int:
    """Assert the given value is a natural (>=0) integer, or raise a ValueError."""
    if not isinstance(value, int) or value < 0:
        raise ValueError(f"{description} must be an integer that is greater or equal to 0")
    return value


def assert_is_slotted(cls: typing.Type[T]) -> typing.Type[T]:
    """Raises a TypeError if the class is not slotted."""
    if not hasattr(cls, "__slots__"):
        raise TypeError(f"Class {cls.__qualname__} is required to be slotted.")
    return cls


def assert_subclasses(cls: typing.Type[T], base: typing.Type[U]) -> typing.Type[T]:
    """Raises a TypeError if `cls` fails to subclass `base`."""
    if not issubclass(cls, base):
        raise TypeError(f"Class {cls.__qualname__} does not subclass {base.__module__}.{base.__qualname__}")
    return cls


def assert_is_instance(obj: typing.Any, cls: typing.Union[typing.Type[T], typing.Tuple[typing.Type[T]]]) -> T:
    """Raises a TypeError if `obj` is not an instance of `cls`, otherwise returns the input `obj` cast to `cls`."""
    if not isinstance(obj, cls):
        raise TypeError(f"Object {obj} was not an instance of expected class {cls}")

    # Noop
    obj: T = obj

    return obj


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
    if not inspect.isclass(cls):
        raise TypeError(f"Object {cls} is marked as a mixin but is not a class")
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

    return cls


def assert_in_range(value, min_inclusive, max_inclusive, name="The value"):
    """Raise a value error if a value is not in the range [min, max]"""
    if not (min_inclusive <= value <= max_inclusive):
        raise ValueError(f"{name} must be in the inclusive range of {min_inclusive} and {max_inclusive}")


__all__ = (
    "assert_not_none",
    "assert_is_slotted",
    "assert_subclasses",
    "assert_is_mixin",
    "assert_in_range",
    "assert_is_natural",
)
