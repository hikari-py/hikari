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
"""Special data structures and utilities.

|internal|
"""

__all__ = [
    "EMPTY_SEQUENCE",
    "EMPTY_SET",
    "EMPTY_COLLECTION",
    "EMPTY_DICT",
    "EMPTY_GENERATOR_EXPRESSION",
    "WeakKeyDictionary",
]

import types
import typing

import weakref

T = typing.TypeVar("T")
K = typing.TypeVar("K", bound=typing.Hashable)
V = typing.TypeVar("V")

EMPTY_SEQUENCE: typing.Final[typing.Sequence[T]] = tuple()
EMPTY_SET: typing.Final[typing.AbstractSet[T]] = frozenset()
EMPTY_COLLECTION: typing.Final[typing.Collection[T]] = tuple()
EMPTY_DICT: typing.Final[typing.Mapping[K, V]] = types.MappingProxyType({})
EMPTY_GENERATOR_EXPRESSION: typing.Final[typing.Iterator[T]] = (_ for _ in EMPTY_COLLECTION)


class WeakKeyDictionary(weakref.WeakKeyDictionary, typing.MutableMapping[K, V]):
    """A dictionary that has weak references to the keys.

    This is a type-safe version of :obj:`~weakref.WeakKeyDictionary`.
    """

    __slots__ = ()
