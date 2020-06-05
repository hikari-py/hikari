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

__all__ = ["Undefined"]

import typing

from hikari.utilities import klass


class Undefined(klass.Singleton):
    """A singleton value that represents an undefined field or argument.

    Undefined will always have a falsy value.

    This type exists to allow differentiation between values that are
    "optional" in the sense that they can be `None` (which is the
    definition of "optional" in Python's `typing` module), and
    values that are truly "optional" in that they may not be present.

    Some cases in Discord's API exist where passing a value as `None` or
    `null` have totally different semantics to not passing the value at all.
    The most noticeable case of this is for "patch" REST endpoints where
    specifying a value will cause it to be updated, but not specifying it
    will result in it being left alone.

    This type differs from `None` in a few different ways. Firstly,
    it will only ever be considered equal to itself, thus the following will
    always be false.

        >>> Undefined() == None
        False

    The type will always be equatable to itself.

        >>> Undefined() == Undefined()
        True

    The second differentiation is that you always instantiate this class to
    obtain an instance of it.

        >>> undefined_value = Undefined()

    ...since this is a singleton, this value will always return the same
    physical object. This improves efficiency.

    The third differentiation is that you can iterate across an undefined value.
    This is used to simplify logic elsewhere. The behaviour of iterating across
    an undefined value is to simply return an iterator that immediately
    completes.

        >>> [*Undefined()]
        []

    This type cannot be mutated, subclassed, or have attributes removed from it
    using conventional methods.
    """

    __slots__ = ()

    def __bool__(self) -> bool:
        return False

    def __iter__(self) -> typing.Iterator[None]:
        yield from ()

    def __init_subclass__(cls, **kwargs: typing.Any) -> typing.NoReturn:
        raise TypeError("Cannot subclass Undefined type")

    def __repr__(self) -> str:
        return f"{type(self).__name__}()"

    def __str__(self) -> str:
        return type(self).__name__.upper()

    def __setattr__(self, _, __) -> typing.NoReturn:
        raise TypeError("Cannot modify Undefined type")

    def __delattr__(self, _) -> typing.NoReturn:
        raise TypeError("Cannot modify Undefined type")

    @staticmethod
    def count(*objs: typing.Any) -> int:
        """Count how many of the given objects are undefined values.

        Returns
        -------
        int
            The number of undefined values given.
        """
        undefined = Undefined()
        return sum(o is undefined for o in objs)
