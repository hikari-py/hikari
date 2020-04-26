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
"""Special data structures and utilities."""

from __future__ import annotations

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

_T = typing.TypeVar("_T")
_K = typing.TypeVar("_K", bound=typing.Hashable)
_V = typing.TypeVar("_V")

EMPTY_SEQUENCE: typing.Final[typing.Sequence[_T]] = tuple()
EMPTY_SET: typing.Final[typing.AbstractSet[_T]] = frozenset()
EMPTY_COLLECTION: typing.Final[typing.Collection[_T]] = tuple()
EMPTY_DICT: typing.Final[typing.Mapping[_K, _V]] = types.MappingProxyType({})
EMPTY_GENERATOR_EXPRESSION: typing.Final[typing.Iterator[_T]] = (_ for _ in EMPTY_COLLECTION)


class WeakKeyDictionary(typing.Generic[_K, _V], weakref.WeakKeyDictionary, typing.MutableMapping[_K, _V]):
    """A dictionary that has weak references to the keys.

    This is a type-safe version of `weakref.WeakKeyDictionary` which is
    subscriptable.

    Examples
    --------
        @attr.s(auto_attribs=True)
        class Commands:
            instances: Set[Command]
            aliases: WeakKeyDictionary[Command, str]
    """

    __slots__ = ()
